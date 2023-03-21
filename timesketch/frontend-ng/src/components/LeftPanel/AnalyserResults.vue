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
      no-gutters
      class="pa-4"
      :style="!(analyzerResults.length) ? '' : 'cursor: pointer'"
      flat
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
        class="ml-1"
        @click.stop=""
      >
        + Run Analyzer
      </v-btn>
      <span class="float-right mr-2">
        <v-progress-circular
          v-if="!analyzerResultsReady"
          :size="20"
          :width="2"
          indeterminate
          color="primary"
        ></v-progress-circular>
        <small v-else><strong>{{ analyzerResults.length }}</strong></small>
      </span>

    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <div v-if="analyzerResults.length > 0">
          <!-- TODO: issue#2565 -->
          <!-- Add a severity and timeline filter here. -->
          <v-data-iterato v-if="analyzerResults.length <= 10" :items="analyzerResults" hide-default-footer disable-pagination>
            <template v-slot:default="props">
              <ts-analyser-result v-for="analyzer in props.items" :key="analyzer.analyzer_name" :analyzer="analyzer" />
            </template>
          </v-data-iterato>
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
              <ts-analyser-result v-for="analyzer in props.items" :key="analyzer.analyzer_name" :analyzer="analyzer" />
            </template>
          </v-data-iterator>
        </div>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import TsAnalyserResult from './AnalyzerResult.vue'

export default {
  props: [],
  components: {
    TsAnalyserResult,
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
    // sketchAnalyzerList() {
    //   return this.$store.state.sketchAnalyzerList
    // },
  },
  mounted() {
    this.analyzerResults = this.$store.state.analyzerResults
    this.analyzerResultsReady = true
  },
}
</script>
