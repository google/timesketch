<!--
Copyright 2023 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
  <div>
    <div
      class="pa-4"
      :style="!(analyzerResults.length) ? '' : 'cursor: pointer'"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span>
        <v-icon left>mdi-auto-fix</v-icon> Analyzer Results
      </span>
      <v-btn
        v-if="expanded || !(analyzerResults.length)"
        :to="{ name: 'Analyze', params: { sketchId: sketch.id } }"
        small
        color="primary"
        left
        text
        @click.stop=""
      >
        + Run Analyzer
      </v-btn>
      <span class="float-right mr-2">
        <v-progress-circular
          v-if="!analyzerResultsReady || activeAnalyzerQueue.length > 0"
          :size="20"
          :width="1"
          indeterminate
          color="primary"
        ></v-progress-circular>
        <small class="ml-1" v-if="analyzerResultsReady"><strong>{{ resultCounter }}</strong></small>
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <div v-if="analyzerResults.length > 0">
          <!-- TODO: issue#2565 -->
          <!-- Add a severity and timeline filter here. -->
          <v-data-iterator v-if="analyzerResults.length <= 10" :items="analyzerResults" hide-default-footer disable-pagination>
            <template v-slot:default="props">
              <ts-analyzer-result v-for="analyzer in props.items" :key="analyzer.analyzerName" :analyzer="analyzer" />
            </template>
          </v-data-iterator>
          <v-data-iterator v-else :items="analyzerResults" hide-default-footer disable-pagination :search="search">
            <template v-slot:header>
              <v-toolbar flat height="45">
                <v-text-field
                  prepend-inner-icon="mdi-filter-variant"
                  v-model="search"
                  clearable
                  hide-details
                  outlined
                  dense
                  label="Filter analyzers"
                ></v-text-field>
              </v-toolbar>
            </template>

            <template v-slot:default="props">
              <ts-analyzer-result v-for="analyzer in props.items" :key="analyzer.analyzerName" :analyzer="analyzer" />
            </template>
          </v-data-iterator>
        </div>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import EventBus from '../../main'
import TsAnalyzerResult from './AnalyzerResult.vue'

export default {
  props: [],
  components: {
    TsAnalyzerResult,
  },
  data: function () {
    return {
      expanded: false,
      search: '',
      analyzerResultsReady: false,
      analyzerResults: [],
      analyzerResultsData: {},
      activeAnalyzerQueue: [],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    analyzerList() {
      return this.$store.state.sketchAnalyzerList
    },
    resultCounter() {
      let counter = 0
      for (const analzyer of this.analyzerResults) {
        for (const timeline in analzyer.data.timelines) {
          if (analzyer.data.timelines[timeline].analysis_status === 'DONE' || analzyer.data.timelines[timeline].analysis_status === 'ERROR') {
            counter += 1
          }
        }
      }
      return counter
    },
  },
  methods: {
    async initializeAnalyzerResults() {
      let sketchAnalyzerSessions = []
      for (const timeline of this.sketch.timelines) {
        const response = await ApiClient.getSketchTimelineAnalysis(this.sketch.id, timeline.id);
        let analyzerSessions = response.data.objects[0]
        if (!analyzerSessions) continue
        sketchAnalyzerSessions = sketchAnalyzerSessions.concat(analyzerSessions)
      }
      this.updateAnalyzerResultsData(sketchAnalyzerSessions)
    },
    updateAnalyzerResultsData(analyzerSessions) {
      let perAnalyzer = this.analyzerResultsData
      try {
        for (const session of analyzerSessions) {
          if (!perAnalyzer[session.analyzer_name]) {
            // the analyzer is not yet in the results: create new entry
            perAnalyzer[session.analyzer_name] = {
              timelines: {},
              analyzerInfo: {
                name: session.analyzer_name,
                description: this.analyzerList[session.analyzer_name].description,
                is_multi: this.analyzerList[session.analyzer_name].is_multi,
                display_name: this.analyzerList[session.analyzer_name].display_name,
              }
            }
          }

          if (!perAnalyzer[session.analyzer_name].timelines[session.timeline.name]) {
            // this timeline is not yet in the results for this analyzer: add it
            perAnalyzer[session.analyzer_name].timelines[session.timeline.name] = {
              id: session.timeline.id,
              name: session.timeline.name,
              color: session.timeline.color,
              verdict: session.result,
              created_at: session.created_at,
              last_analysissession_id: session.analysissession_id,
              analysis_status: session.status[0].status,
            }
          }

          if (perAnalyzer[session.analyzer_name].timelines[session.timeline.name].last_analysissession_id < session.analysissession_id) {
            // this timeline is already in the results for this analyzer but check if the session is newer and update it
            perAnalyzer[session.analyzer_name].timelines[session.timeline.name].created_at = session.created_at
            perAnalyzer[session.analyzer_name].timelines[session.timeline.name].verdict = session.result
            perAnalyzer[session.analyzer_name].timelines[session.timeline.name].last_analysissession_id = session.analysissession_id
            perAnalyzer[session.analyzer_name].timelines[session.timeline.name].analysis_status = session.status[0].status
          }

          if (session.status[0].status === 'PENDING' || session.status[0].status === 'STARTED') {
            // if the session is PENDING or STARTED, add the session to the queue (if not there yet)
            if (this.activeAnalyzerQueue.indexOf(session.analysissession_id) === -1) this.activeAnalyzerQueue.push(session.analysissession_id)
          }
          if (session.status[0].status === 'DONE' || session.status[0].status === 'ERROR') {
            // if the session is DONE or ERROR, remove it from the queue
            const index = this.activeAnalyzerQueue.indexOf(session.analysissession_id)
            if (index > -1) this.activeAnalyzerQueue.splice(index, 1)
          }
        }
      } catch(e) {
        console.error(e)
      }

      // for now sort the results in alphabetical order. In the future this will be sorted by verdict severity.
      this.analyzerResultsData = perAnalyzer
      let sortedAnalyzerList = [...Object.entries(perAnalyzer).map(([analyzerName, data]) => ({analyzerName, data}))]
      sortedAnalyzerList.sort((a, b) => a.data.analyzerInfo.display_name.localeCompare(b.data.analyzerInfo.display_name))
      this.analyzerResults = sortedAnalyzerList
      this.analyzerResultsReady = true
    },
    async fetchActiveSessions() {
      const response = await ApiClient.getActiveAnalyzerSessions(this.sketch.id)
      let activeSessions = response.data.objects[0]['sessions']
      if (activeSessions) {
        activeSessions.forEach(sessionId => {
          if (this.activeAnalyzerQueue.indexOf(sessionId) === -1) this.activeAnalyzerQueue.push(sessionId)
        })
      }
    },
    async fetchAnalyzerSessionData() {
      let activeAnalyzerSessionData = []
      for (const sessionId of this.activeAnalyzerQueue) {
        const response = await ApiClient.getAnalyzerSession(this.sketch.id, sessionId)
        let analyzerSession = response.data.objects[0]
        if (!analyzerSession) continue
        activeAnalyzerSessionData.push(...analyzerSession['analyses'])
      }
      this.updateAnalyzerResultsData(activeAnalyzerSessionData)
    },
    triggeredAnalyzerRuns: function (data) {
      data.forEach(sessionId => {
        if (this.activeAnalyzerQueue.indexOf(sessionId) === -1) this.activeAnalyzerQueue.push(sessionId)
      })
    },
  },
  mounted() {
    EventBus.$on('triggeredAnalyzerRuns', this.triggeredAnalyzerRuns)
    this.initializeAnalyzerResults()
  },
  beforeDestroy() {
    EventBus.$off('triggeredAnalyzerRuns')
    clearInterval(this.interval)
    this.interval = false
  },
  watch: {
    activeAnalyzerQueue: function (sessionQueue) {
      if (sessionQueue.length > 0 && !this.interval) {
        this.interval = setInterval(function() {
          if (sessionQueue.length > 0) {
            // fetch data for sessions in the queue
            this.fetchAnalyzerSessionData()
            // update active session queue
            this.fetchActiveSessions()
          } else {
            // the queue is empty so stop the interval
            clearInterval(this.interval)
            this.interval = false
          }
        }.bind(this),
        5000)
      }
    },
  },
}
</script>
