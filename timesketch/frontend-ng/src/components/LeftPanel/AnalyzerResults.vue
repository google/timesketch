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
          v-if="!analyzerResultsReady"
          :size="20"
          :width="1"
          indeterminate
          color="primary"
        ></v-progress-circular>
        <small class="ml-1" v-if="analyzerResultsReady"><strong>{{ analyzerResultdCounter }}</strong></small>
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
      analyzerResultsCounter: 0,
    }
  },
  // TODO: Have an automatic poll for new analyzers running when they are triggered.
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
  },
  methods: {
    async updateAnalyzerResultsData() {
      let perAnalyzer = {}
      let resultCounter = 0
      for (const timeline of this.sketch.timelines) {
        try {
          const response = await ApiClient.getSketchTimelineAnalysis(this.sketch.id, timeline.id);
          let analyzerSessions = response.data.objects[0]
          analyzerSessions.forEach((session) => {
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
              resultCounter += 1
            }

            if (perAnalyzer[session.analyzer_name].timelines[session.timeline.name].last_analysissession_id < session.analysissession_id) {
              // this timeline is already in the results for this analyzer but check if the session is newer and update it
              perAnalyzer[session.analyzer_name].timelines[session.timeline.name].created_at = session.created_at
              perAnalyzer[session.analyzer_name].timelines[session.timeline.name].verdict = session.result
              perAnalyzer[session.analyzer_name].timelines[session.timeline.name].last_analysissession_id = session.analysissession_id
              perAnalyzer[session.analyzer_name].timelines[session.timeline.name].status = session.status[0].status
            }
          })
        } catch(e) {
          console.error(e)
        }
      }
      // for now sort the results in alphabetical order. In the future this will be sorted by verdict severity.
      let sortedAnalyzerList = [...Object.entries(perAnalyzer).map(([analyzerName, data]) => ({analyzerName, data}))]
      sortedAnalyzerList.sort((a, b) => a.data.analyzerInfo.display_name.localeCompare(b.data.analyzerInfo.display_name))
      this.analyzerResults = sortedAnalyzerList
      this.analyzerResultdCounter = resultCounter
      this.analyzerResultsReady = true
    }
  },
  mounted() {
    this.updateAnalyzerResultsData()
  },
}
</script>
