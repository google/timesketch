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
                <div v-on="on" class="d-inline-block">
                  <v-btn
                    icon
                    color="primary"
                    :disabled="(timelineSelection.length > 0) ? false : true"
                    @click="runAnalyzer(analyzer.analyzerName)"
                  >
                    <v-icon>mdi-play-circle-outline</v-icon>
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
import EventBus from '../../main'

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
    sortedAnalyzerList() {
      let unsortedAnalyzerList = Object.entries(this.analyzerList).map(([analyzerName, info]) => ({analyzerName, info}))
      let sortedAnalyzerList = [...unsortedAnalyzerList]
      sortedAnalyzerList.sort((a, b) => a.info.display_name.localeCompare(b.info.display_name))
      return sortedAnalyzerList
    }
  },
  methods: {
    runAnalyzer(analyzerName) {
      ApiClient.runAnalyzers(this.sketch.id,  this.timelineSelection, [analyzerName])
        .then((response) => {
          let sessionIds = []
          for (let sessions of response.data.objects[0]) {
            sessionIds.push(sessions.id)
          }
          this.triggeredAnalyzerRuns(sessionIds)
        })
        .catch((error) => {
          console.log(error)
        })
    },
    triggeredAnalyzerRuns(data) {
      EventBus.$emit('triggeredAnalyzerRuns', data)
    }
  },
}
</script>
