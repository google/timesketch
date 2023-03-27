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
        <small class="ml-1" v-if="analyzerResultsReady"><strong>{{ totalNumberOfAnalyzerResults }}</strong></small>
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <div v-if="analyzerResults.length > 0">
          <!-- TODO: issue#2565 -->
          <!-- Add a severity and timeline filter here. -->
          <v-data-iterator v-if="analyzerResults.length <= 10" :items="analyzerResults" hide-default-footer disable-pagination>
            <template v-slot:default="props">
              <ts-analyser-result v-for="analyzer in props.items" :key="analyzer.analyzer_name" :analyzer="analyzer" />
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
              <ts-analyzer-result v-for="analyzer in props.items" :key="analyzer.analyzer_name" :analyzer="analyzer" />
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
      analyzerResultsReady: false,
      analyzerResults: [],
      search: '',
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
    totalNumberOfAnalyzerResults() {
      let counter = 0
      this.analyzerResults.forEach((analyzer) => {
        counter += analyzer.timelines.length
      })
      return counter
    },
  },
  methods: {
    getAnalyzerResults() {
      let analyzerResults = []
      this.sketch.timelines.forEach(timeline => {
        ApiClient.getSketchTimelineAnalysis(this.sketch.id, timeline.id)
        .then(response => {
          if (response.data.objects[0] !== undefined) {
            // massage data to fit the result list needs
            response.data.objects[0].forEach((analysis) => {
              let analyzerExists = false
              analyzerResults.every((analyzer) => {
                if (analyzer.analyzer_name === analysis.analyzer_name) {
                  analyzerExists = true
                  // analyzer already exists in the list
                  let timelineExists = false
                  analyzer.timelines.every((timeline) => {
                    // timeline already exists in the list
                    if (timeline.id === analysis.timeline.id) {
                      timelineExists = true
                      // check if the analysis is newer than the one in the list
                      if (analysis.created_at > timeline.created_at) {
                        timeline.created_at = analysis.created_at
                        timeline.result = analysis.result
                        timeline.status = analysis.status[0].status
                      }
                      return false
                    }
                    return true
                  })
                  if (!timelineExists) {
                    // timeline did not exist so add it
                    let output = {
                      id: analysis.timeline.id,
                      name: analysis.timeline.name,
                      color: '#'+analysis.timeline.color,
                      result: analysis.result,
                      status: analysis.status[0].status,
                      created_at: analysis.created_at
                    }
                    analyzer.timelines.push(output)
                  }
                  return false
                }
                return true
              })
              if (!analyzerExists) {
                // analyzer did not exist so add it
                let output = {
                  analyzer_name: analysis.analyzer_name,
                  analyzer_display_name: this.analyzerList[analysis.analyzer_name].display_name,
                  analyzer_is_multi: this.analyzerList[analysis.analyzer_name].is_multi,
                  timelines: [
                    {
                      id: analysis.timeline.id,
                      name: analysis.timeline.name,
                      color: '#'+analysis.timeline.color,
                      result: analysis.result,
                      status: analysis.status[0].status,
                      created_at: analysis.created_at
                    },
                  ],
                }
                analyzerResults.push(output)
              }
            })
          }
        })
        .catch(e => {
          console.error(e)
        })
        this.analyzerResults = analyzerResults
        this.analyzerResultsReady = true
      })
    },
  },
  mounted() {
    this.getAnalyzerResults()
  },
}
</script>
