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
      :style="!analyzerResults.length ? '' : 'cursor: pointer'"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> <v-icon left>mdi-auto-fix</v-icon> Analyzer Results </span>
      <v-btn
        v-if="expanded || (analyzerResults && !analyzerResults.length && analyzerResultsReady)"
        icon
        text
        class="float-right mt-n1 mr-n1"
        :to="{ name: 'Analyze', params: { sketchId: sketch.id, analyzerTimelineId: undefined } }"
        @click.stop=""
      >
        <v-icon>mdi-plus</v-icon>
      </v-btn>
      <span class="float-right" style="margin-right: 3px">
        <v-progress-circular
          v-if="!analyzerResultsReady || (activeAnalyzerQueue.length > 0 && !activeAnalyzerTimeoutTriggered)"
          :size="24"
          :width="1"
          indeterminate
          :value="activeAnalyzerDisplayCount"
          >{{ activeAnalyzerDisplayCount }}</v-progress-circular
        >
        <v-tooltip v-if="activeAnalyzerTimeoutTriggered" top>
          <template v-slot:activator="{ on }">
            <v-btn
              v-on="on"
              small
              icon
              @click.stop=""
              @click="triggeredAnalyzerRuns(activeAnalyzerQueue)"
            >
              <v-icon small>mdi-reload-alert</v-icon>
            </v-btn>
          </template>
          <span>analyzer status check timeout, click to reload</span>
        </v-tooltip>
      </span>
      <span class="float-right" style="margin-right: 10px">
        <small class="ml-3" v-if="!expanded && analyzerResults && analyzerResults.length && analyzerResultsReady"
          ><strong>{{ resultCounter }}</strong></small
        >
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <div v-if="analyzerResults.length > 0">
          <!-- TODO: issue#2565 -->
          <!-- Add a severity and timeline filter here. -->
          <v-data-iterator
            v-if="analyzerResults.length <= 10"
            :items="analyzerResults"
            hide-default-footer
            disable-pagination
          >
            <template v-slot:default="props">
              <ts-analyzer-result v-for="analyzer in props.items" :key="analyzer.analyzerName" :analyzer="analyzer" />
            </template>
          </v-data-iterator>
          <v-data-iterator
            v-else
            :items="analyzerResults"
            hide-default-footer
            disable-pagination
            :search="search"
            :custom-filter="filterAnalyzers"
          >
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
      activeAnalyzerInterval: 15000, // milliseconds
      activeAnalyzerTimeout: 300000, // milliseconds
      activeAnalyzerTimeoutTriggered: false,
      activeAnalyzerTimerStart: null,
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
          if (
            analzyer.data.timelines[timeline].analysis_status === 'DONE' ||
            analzyer.data.timelines[timeline].analysis_status === 'ERROR'
          ) {
            counter += 1
          }
        }
      }
      return counter
    },
    activeAnalyzerDisplayCount() {
      return this.activeAnalyzerQueue.length > 0 ? this.activeAnalyzerQueue.length : ''
    },
  },
  methods: {
    async initializeAnalyzerResults() {
      let sketchAnalyzerSessions = []
      for (const timeline of this.sketch.timelines) {
        const response = await ApiClient.getSketchTimelineAnalysis(this.sketch.id, timeline.id)
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
            // There is an edge case where the analyzer is not in the analyzer list.
            // If this happens, fall back to the analyzer short name. Tracked in issue#2738
            if (this.analyzerList[session.analyzer_name]) {
              perAnalyzer[session.analyzer_name] = {
                timelines: {},
                analyzerInfo: {
                  name: session.analyzer_name,
                  description: this.analyzerList[session.analyzer_name].description,
                  is_multi: this.analyzerList[session.analyzer_name].is_multi,
                  display_name: this.analyzerList[session.analyzer_name].display_name,
                },
              }
            } else {
              perAnalyzer[session.analyzer_name] = {
                timelines: {},
                analyzerInfo: {
                  name: session.analyzer_name,
                  description: 'No description available.',
                  is_multi: false,
                  display_name: session.analyzer_name,
                },
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

          if (
            perAnalyzer[session.analyzer_name].timelines[session.timeline.name].last_analysissession_id <
            session.analysissession_id
          ) {
            // this timeline is already in the results for this analyzer but check if the session is newer and update it
            perAnalyzer[session.analyzer_name].timelines[session.timeline.name].created_at = session.created_at
            perAnalyzer[session.analyzer_name].timelines[session.timeline.name].verdict = session.result
            perAnalyzer[session.analyzer_name].timelines[session.timeline.name].last_analysissession_id =
              session.analysissession_id
            perAnalyzer[session.analyzer_name].timelines[session.timeline.name].analysis_status =
              session.status[0].status
          }

          if (session.status[0].status === 'PENDING' || session.status[0].status === 'STARTED') {
            // if the session is PENDING or STARTED, add the session to the queue (if not there yet)
            if (this.activeAnalyzerQueue.indexOf(session.analysissession_id) === -1) {
              this.activeAnalyzerQueue.push(session.analysissession_id)
            }
          }
          if (session.status[0].status === 'DONE' || session.status[0].status === 'ERROR') {
            // if the session is DONE or ERROR, remove it from the queue
            const index = this.activeAnalyzerQueue.indexOf(session.analysissession_id)
            if (index > -1) this.activeAnalyzerQueue.splice(index, 1)
          }
        }
      } catch (e) {
        console.error(e)
      }

      // for now sort the results in alphabetical order. In the future this will be sorted by verdict severity.
      this.analyzerResultsData = perAnalyzer
      let sortedAnalyzerList = [...Object.entries(perAnalyzer).map(([analyzerName, data]) => ({ analyzerName, data }))]
      sortedAnalyzerList.sort((a, b) =>
        a.data.analyzerInfo.display_name.localeCompare(b.data.analyzerInfo.display_name)
      )
      this.analyzerResults = sortedAnalyzerList
      this.analyzerResultsReady = true
    },
    fetchActiveAnalyzerSessions() {
      ApiClient.getActiveAnalyzerSessions(this.sketch.id).then((response) => {
        const activeSessionsDetailed = response.data.objects[0].detailed_sessions
        this.activeAnalyzerQueue = response.data.objects[0].sessions
        let activeAnalyzerSessionData = []
        if (activeSessionsDetailed.length > 0) {
          for (const session of activeSessionsDetailed) {
            activeAnalyzerSessionData.push(...session.objects[0]['analyses'])
          }
        }
        this.updateAnalyzerResultsData(activeAnalyzerSessionData)
      }).catch((error) => {
        console.error(error)
      })

    },
    triggeredAnalyzerRuns: function (data) {
      this.activeAnalyzerTimerStart = Date.now()
      data.forEach((sessionId) => {
        if (this.activeAnalyzerQueue.indexOf(sessionId) === -1) this.activeAnalyzerQueue.push(sessionId)
      })
      this.fetchActiveAnalyzerSessions()
    },
    filterAnalyzers(items, search) {
      const searchStr = (search || '').toLowerCase()
      return (
        items &&
        items.filter((item) => {
          const displayNameMatches = item.data.analyzerInfo.display_name.toLowerCase().indexOf(searchStr) !== -1
          const timelineNameMatches = Object.keys(item.data.timelines).find(
            (timelineName) => timelineName.indexOf(searchStr) !== -1
          )
          return displayNameMatches || timelineNameMatches
        })
      )
    },
  },
  mounted() {
    EventBus.$on('triggeredAnalyzerRuns', this.triggeredAnalyzerRuns)
    this.initializeAnalyzerResults()
    this.activeAnalyzerTimerStart = Date.now()
  },
  beforeDestroy() {
    EventBus.$off('triggeredAnalyzerRuns')
    clearInterval(this.interval)
    this.interval = false
  },
  watch: {
    activeAnalyzerQueue: function (sessionQueue) {
      if (sessionQueue.length > 0 && !this.interval) {
        this.interval = setInterval(
          function () {
            if (sessionQueue.length === 0 || this.activeAnalyzerQueue.length === 0) {
              // the queue is empty so stop the interval
              clearInterval(this.interval)
              this.activeAnalyzerTimerStart = null
              this.interval = false
              return
            }
            // check if the timeout of the interval has been reached.
            // This prevents the analyzer frontwend from checking stuck anayzers indefinetly.
            if (this.activeAnalyzerTimerStart !== null && (Date.now() - this.activeAnalyzerTimerStart > this.activeAnalyzerTimeout)) {
              clearInterval(this.interval)
              this.interval = false
              this.activeAnalyzerTimerStart = null
              this.activeAnalyzerTimeoutTriggered = true
              return
            }
            // fetch active analyzer sessions
            this.fetchActiveAnalyzerSessions()
          }.bind(this),
          this.activeAnalyzerInterval
        )
      }
    },
  },
}
</script>

<style scoped lang="scss">
.v-progress-circular {
  font-size: 12px;
}
</style>

