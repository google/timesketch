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
  <v-simple-table>
    <template v-slot:default>
      <thead>
        <tr>
          <th></th>
          <th class="text-left">
            Name
          </th>
          <th class="text-left">
            Description
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="analyzer in sortedAnalyzerList"
          :key="analyzer.analyzerName"
        >
          <td>
            <v-tooltip right open-delay="500">
              <template v-slot:activator="{ on }">
                <div v-on="on" class="d-inline-block d-flex justify-center pr-4">
                  <v-progress-circular
                    v-if="isLoading(analyzer.analyzerName)"
                    :size="20"
                    :width="2"
                    indeterminate
                    color="primary"
                  >
                  </v-progress-circular>
                  <v-btn
                    v-if="!isLoading(analyzer.analyzerName)"
                    icon
                    color="primary"
                    :disabled="(timelineSelection.length > 0) ? false : true"
                    @click="runAnalyzer(analyzer.analyzerName)"
                  >
                    <v-icon v-if="!showRerunIcon(analyzer.analyzerName)">
                      mdi-play-circle-outline
                    </v-icon>
                    <v-icon v-else>mdi-replay</v-icon>
                  </v-btn>
                </div>
              </template>
              <span v-if="timelineSelection.length === 0">Please select a timeline above first.</span>
              <span v-else-if="showRerunIcon(analyzer.analyzerName)" >Re-run analyzer: "{{ analyzer.info.display_name }}"</span>
              <span v-else>Run analyzer: "{{ analyzer.info.display_name }}"</span>
            </v-tooltip>
          </td>
          <td>{{ analyzer.info.display_name}}</td>
          <td>{{ analyzer.info.description }}</td>
        </tr>
      </tbody>
    </template>
  </v-simple-table>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

const LOADING_INDICATOR_DURATION_MS = 3000;

export default {
  props: ['timelineSelection'],
  data() {
    return {
      /** Currently triggered analyzers. Used for showing run or re-run icons. */
      triggeredAnalyzers: [],
      /**
       * Analyzers that should show loading indicators. Those are triggered
       * analyzers for a duration of LOADING_INDICATOR_DURATION_MS.
       */
      loadingAnalyzers: []
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    analyzerList() {
        return this.$store.state.sketchAnalyzerList
    },
    analyzerResults() {
        return this.$store.state.analyzerResults
    },
    analyzersAlreadyRun() {
      // create a set for a faster lookup
      const timelineSelectionSet = new Set(this.timelineSelection)
      const analyzersOnSelectedTimelines = this.analyzerResults.filter(res => timelineSelectionSet.has(res.timeline.id))
      const analyzerRanOnTimelines = new Map()
      for (const res of analyzersOnSelectedTimelines) {
        if (!analyzerRanOnTimelines.has(res.analyzer_name)) {
          analyzerRanOnTimelines.set(res.analyzer_name, new Set())
        }
        analyzerRanOnTimelines.get(res.analyzer_name).add(res.timeline.id)
      }

      const analyzerSet = new Set()
      for (const [analyzerName, timelineSet] of analyzerRanOnTimelines) {
        if (timelineSet.size === timelineSelectionSet.size) {
          analyzerSet.add(analyzerName)
        }
      }

      this.triggered.forEach(analyzer => analyzerSet.has(analyzer) ? null : analyzerSet.add(analyzer))
      this.resetTriggeredAnalyzers()
      
      return analyzerSet

    },
    activeAnalyzerTimelinesMap() {
        const byAnalyzerMap = new Map()
        for (const analysis of this.$store.state.activeAnalyses) {
          if (!byAnalyzerMap.has(analysis.analyzer_name)) {
            byAnalyzerMap.set(analysis.analyzer_name, new Set())
          }
          byAnalyzerMap.get(analysis.analyzer_name).add(analysis.timeline.id)
        }
        return byAnalyzerMap
    },
    sortedAnalyzerList() {
      let unsortedAnalyzerList = Object.entries(this.analyzerList).map(([analyzerName, info]) => ({analyzerName, info}))
      let sortedAnalyzerList = [...unsortedAnalyzerList]
      sortedAnalyzerList.sort((a, b) => a.info.display_name.localeCompare(b.info.display_name))
      return sortedAnalyzerList
    },
    triggered() {
      return this.triggeredAnalyzers
    },
    loading() {
      return this.loadingAnalyzers
    }
  },
  methods: {
    isLoading(analyzerName) {
      return this.loading.includes(analyzerName)
    },
    showRerunIcon(analyzerName) {
      return this.analyzersAlreadyRun.has(analyzerName)
    },
    activeTimelinesCount(analyzerName) {
      const timelinesSet = this.activeAnalyzerTimelinesMap.get(analyzerName)
      return timelinesSet ? timelinesSet.size : 0
    },
    runAnalyzer(analyzerName) {
      this.triggeredAnalyzers = [...this.triggeredAnalyzers, analyzerName]
      this.loadingAnalyzers = [...this.loadingAnalyzers, analyzerName]

      // Hide loading indicator after max LOADING_INDICATOR_DURATION_MS.
      setTimeout(() => {
        this.removeFromLoading(analyzerName)
      }, LOADING_INDICATOR_DURATION_MS)

      // The loading indicator should stay at least LOADING_INDICATOR_DURATION_MS.
      const analyzerTriggeredTime = new Date().getTime()

      ApiClient.runAnalyzers(this.sketch.id,  this.timelineSelection, [analyzerName])
        .then((response) => {
          let analyses = []
          let sessionIds = []
          for (let session of response.data.objects[0]) {
            sessionIds.push(session.id)
            analyses = analyses.concat(session.analyses)
          }
          this.$store.dispatch('addActiveAnalyses', analyses)

          // Call took at least LOADING_INDICATOR_DURATION_MS, so we can hide the loading indicator.
          if (new Date().getTime() - analyzerTriggeredTime >= LOADING_INDICATOR_DURATION_MS) {
            this.removeFromLoading(analyzerName)
          }
        })
        .catch((error) => {
          console.log(error)
        })
    },
    removeFromLoading(analyzerName) {
      this.loadingAnalyzers = this.loadingAnalyzers.filter(a => analyzerName !== a)
    },
    resetTriggeredAnalyzers() {
      this.triggeredAnalyzers = []
    }
  },
}
</script>
