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
                    v-if="isActive(analyzer.analyzerName)"
                    :size="20"
                    :width="2"
                    :value="activeTimelinesCount(analyzer.analyzerName)"
                    indeterminate
                    color="primary"
                  >
                    {{ activeTimelinesCount(analyzer.analyzerName)}}
                  </v-progress-circular>
                  <v-btn
                    v-if="!isActive(analyzer.analyzerName)"
                    icon
                    color="primary"
                    :disabled="(timelineSelection.length > 0) ? false : true"
                    @click="runAnalyzer(analyzer.analyzerName)"
                  >
                    <v-icon
                      v-if="!analyzersAlreadyRun.has(analyzer.analyzerName)"
                    >
                      mdi-play-circle-outline
                    </v-icon>
                    <v-icon v-else>mdi-replay</v-icon>
                  </v-btn>
                </div>
              </template>
              <span v-if="timelineSelection.length > 0">Run analyzer: {{ analyzer.info.display_name }}</span>
              <span v-else>Please select a timeline above first.</span>
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

export default {
  props: ['timelineSelection'],
  data() {
    return {
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch;
    },
    analyzerList() {
        return this.$store.state.sketchAnalyzerList;
    },
    analyzerResults() {
        return this.$store.state.analyzerResults;
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
      return analyzerSet

    },
    activeAnalyzerTimelinesMap() {
        const byAnalyzerMap = new Map();
        for (const analysis of this.$store.state.activeAnalyses) {
          if (!byAnalyzerMap.has(analysis.analyzer_name)) {
            byAnalyzerMap.set(analysis.analyzer_name, new Set());
          }
          byAnalyzerMap.get(analysis.analyzer_name).add(analysis.timeline.id);
        }
        return byAnalyzerMap;
    },
    sortedAnalyzerList() {
      let unsortedAnalyzerList = Object.entries(this.analyzerList).map(([analyzerName, info]) => ({analyzerName, info}))
      let sortedAnalyzerList = [...unsortedAnalyzerList]
      sortedAnalyzerList.sort((a, b) => a.info.display_name.localeCompare(b.info.display_name))
      return sortedAnalyzerList
    }
  },
  methods: {
    isActive(analyzerName) {
      return this.activeTimelinesCount(analyzerName) > 0
    },
    activeTimelinesCount(analyzerName) {
      const timelinesSet = this.activeAnalyzerTimelinesMap.get(analyzerName)
      return timelinesSet ? timelinesSet.size : 0
    },
    runAnalyzer(analyzerName) {
      ApiClient.runAnalyzers(this.sketch.id,  this.timelineSelection, [analyzerName])
        .then((response) => {
          let analyses = [];
          let sessionIds = []
          for (let session of response.data.objects[0]) {
            sessionIds.push(session.id)
            analyses = analyses.concat(session.analyses)
          }
          this.$store.dispatch('addActiveAnalyses', analyses)
        })
        .catch((error) => {
          console.log(error)
        })
    },
  },
}
</script>
