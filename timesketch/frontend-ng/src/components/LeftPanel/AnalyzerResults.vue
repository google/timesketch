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
      :style="!sortedAnalyzerResults.length ? '' : 'cursor: pointer'"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> <v-icon left>mdi-auto-fix</v-icon> Analyzer Results </span>
      <v-btn
        v-if="expanded || (sortedAnalyzerResults && !sortedAnalyzerResults.length && analyzerResultsReady)"
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
          v-if="!analyzerResultsReady || (activeAnalyzerSessionIds.length > 0 && !activeAnalyzerTimeoutTriggered)"
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
              @click="startPolling()"
            >
              <v-icon small>mdi-reload-alert</v-icon>
            </v-btn>
          </template>
          <span>analyzer status check timeout, click to reload</span>
        </v-tooltip>
      </span>
      <span class="float-right" style="margin-right: 10px">
        <small class="ml-3" v-if="!expanded && sortedAnalyzerResults && sortedAnalyzerResults.length && analyzerResultsReady"
          ><strong>{{ resultCounter }}</strong></small
        >
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <div v-if="sortedAnalyzerResults.length > 0">
          <!-- TODO: issue#2565 -->
          <!-- Add a severity and timeline filter here. -->
          <v-data-iterator
            v-if="sortedAnalyzerResults.length <= 10"
            :items="sortedAnalyzerResults"
            hide-default-footer
            disable-pagination
          >
            <template v-slot:default="props">
              <ts-analyzer-result
                v-for="analyzer in props.items"
                :key="analyzer.analyzerName"
                :analyzer="analyzer"
                :isActive="activeAnalyzers.has(analyzer.analyzerName)"
              ></ts-analyzer-result>
            </template>
          </v-data-iterator>
          <v-data-iterator
            v-else
            :items="sortedAnalyzerResults"
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
              <ts-analyzer-result
                v-for="analyzer in props.items"
                :key="analyzer.analyzerName"
                :analyzer="analyzer"
                :isActive="activeAnalyzers.has(analyzer.analyzerName)"
              ></ts-analyzer-result>
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
    activeAnalyses() {
      return this.$store.state.activeAnalyses
    },
    analyzerResults() {
      return this.$store.state.analyzerResults
    },
    sortedAnalyzerResults() {
      const perAnalyzer = this.groupByAnalyzer([
        ...this.analyzerResults,
        ...this.activeAnalyses,
      ])
      // for now sort the results in alphabetical order. In the future this will be sorted by verdict severity.
      let sortedAnalyzerList = [...Object.entries(perAnalyzer).map(([analyzerName, data]) => ({ analyzerName, data }))]
      sortedAnalyzerList.sort((a, b) =>
        a.data.analyzerInfo.display_name.localeCompare(b.data.analyzerInfo.display_name)
      )
      return sortedAnalyzerList
    },
    resultCounter() {
      let counter = 0
      for (const analyzer of this.sortedAnalyzerResults) {
        for (const timeline in analyzer.data.timelines) {
          if (
            analyzer.data.timelines[timeline].analysis_status === 'DONE' ||
            analyzer.data.timelines[timeline].analysis_status === 'ERROR'
          ) {
            counter += 1
          }
        }
      }
      return counter
    },
    activeAnalyzers() {
      return new Set(this.activeAnalyses.map(a => a.analyzer_name))
    },
    activeAnalyzerSessionIds() {
      return Array.from(new Set(this.activeAnalyses.map(a => a.analysissession_id)))
    },
    activeAnalyzerDisplayCount() {
      return this.activeAnalyzerSessionIds.length > 0 ? this.activeAnalyzerSessionIds.length : ''
    },
  },
  methods: {
    async initializeAnalyzerResults() {
      let allAnalyses = []
      for (const timeline of this.sketch.timelines) {
        const response = await ApiClient.getSketchTimelineAnalysis(this.sketch.id, timeline.id)
        let analyses = response.data.objects[0]
        if (!analyses) continue
        allAnalyses = allAnalyses.concat(analyses)
      }
      this.$store.dispatch('updateAnalyzerResults', allAnalyses)
      this.updateActiveAnalyses(this.$store, allAnalyses)
    },
    groupByAnalyzer(analyses) {
      let perAnalyzer = {}
      for (const analysis of analyses) {
        if (!perAnalyzer[analysis.analyzer_name]) {
          // the analyzer is not yet in the results: create new entry
          // There is an edge case where the analyzer is not in the analyzer list.
          // If this happens, fall back to the analyzer short name. Tracked in issue#2738
          if (this.analyzerList[analysis.analyzer_name]) {
            perAnalyzer[analysis.analyzer_name] = {
              timelines: {},
              analyzerInfo: {
                name: analysis.analyzer_name,
                description: this.analyzerList[analysis.analyzer_name].description,
                is_multi: this.analyzerList[analysis.analyzer_name].is_multi,
                display_name: this.analyzerList[analysis.analyzer_name].display_name,
              },
            }
          } else {
            perAnalyzer[analysis.analyzer_name] = {
              timelines: {},
              analyzerInfo: {
                name: analysis.analyzer_name,
                description: 'No description available.',
                is_multi: false,
                display_name: analysis.analyzer_name,
              },
            }
          }
        }

        if (!perAnalyzer[analysis.analyzer_name].timelines[analysis.timeline.name]) {
          // this timeline is not yet in the results for this analyzer: add it
          perAnalyzer[analysis.analyzer_name].timelines[analysis.timeline.name] = {
            id: analysis.timeline.id,
            name: analysis.timeline.name,
            color: analysis.timeline.color,
            verdict: analysis.result,
            created_at: analysis.created_at,
            last_analysissession_id: analysis.analysissession_id,
            analysis_status: analysis.status[0].status,
          }
        }

        if (
          perAnalyzer[analysis.analyzer_name].timelines[analysis.timeline.name].last_analysissession_id <
          analysis.analysissession_id
        ) {
          // this timeline is already in the results for this analyzer but check if the session is newer and update it
          perAnalyzer[analysis.analyzer_name].timelines[analysis.timeline.name].created_at = analysis.created_at
          perAnalyzer[analysis.analyzer_name].timelines[analysis.timeline.name].verdict = analysis.result
          perAnalyzer[analysis.analyzer_name].timelines[analysis.timeline.name].last_analysissession_id =
            analysis.analysissession_id
          perAnalyzer[analysis.analyzer_name].timelines[analysis.timeline.name].analysis_status =
            analysis.status[0].status
        }
      }
      return perAnalyzer
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
    startPolling() {
      if (this.activeAnalyzerSessionIds.length > 0 && !this.interval) {
        this.activeAnalyzerTimerStart = Date.now()
        this.interval = setInterval(
          async function () {
            if (this.activeAnalyzerSessionIds.length === 0) {
              // the queue is empty so stop the interval
              this.stopPolling()
              this.initializeAnalyzerResults()
              return
            }
            // check if the timeout of the interval has been reached.
            // This prevents the analyzer frontend from checking stuck anayzers indefinetly.
            if (this.activeAnalyzerTimerStart !== null && (Date.now() - this.activeAnalyzerTimerStart > this.activeAnalyzerTimeout)) {
              this.stopPolling()
              this.activeAnalyzerTimeoutTriggered = true
              return
            }
            const lastActiveCount = this.activeAnalyses.length
            const activeAnalyses = await this.fetchActiveAnalyses(this.$store, this.sketch.id)

            // Refetch analyzer results if some analyzer finished.
            if (lastActiveCount !== activeAnalyses.length) {
              this.initializeAnalyzerResults()
            } else {
              this.updateActiveAnalyses(activeAnalyses)
            }
          }.bind(this),
          this.activeAnalyzerInterval
        )
      }
    },
    stopPolling() {
      clearInterval(this.interval)
      this.activeAnalyzerTimerStart = null
      this.interval = false
    },
    async fetchActiveAnalyses(sketchId) {
      try {
        const activeAnalyses = []
        const response = await ApiClient.getActiveAnalyzerSessions(sketchId)
        if (response && response.data && response.data.objects && response.data.objects[0]) {
          const activeSessionsDetailed = response.data.objects[0].detailed_sessions
          if (activeSessionsDetailed.length > 0) {
            for (const session of activeSessionsDetailed) {
              activeAnalyses.push(...session.objects[0]['analyses'])
            }
          }
        }
        return activeAnalyses;
      } catch (error) {
        console.error(error);
      }
    },
    updateActiveAnalyses(store, analyses) {
      const activeAnalyses = analyses.filter(a => a.status[0].status === 'PENDING' || a.status[0].status === 'STARTED');
      store.dispatch("updateActiveAnalyses", activeAnalyses)
    }
  },
  mounted() {
    this.initializeAnalyzerResults()
    this.analyzerResultsReady = true
    this.activeAnalyzerTimerStart = Date.now()
  },
  beforeDestroy() {
    clearInterval(this.interval)
    this.interval = false
  },
  watch: {
    activeAnalyzerSessionIds: function () {
      this.startPolling();
    },
  },
}
</script>

<style scoped lang="scss">
.v-progress-circular {
  font-size: 12px;
}
</style>

