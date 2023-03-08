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
      style="cursor: pointer"
      flat
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span>
        <v-icon left>mdi-auto-fix</v-icon> Analyzer Results
      </span>
      <v-btn
        v-if="expanded"
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
        <small><strong>{{ analyzerResults.length }}</strong></small>
      </span>

    </div>
    <v-expand-transition>
      <div v-if="analyzerResults.length > 0" v-show="expanded">
        <!-- TODO: issue#2565 -->
        <ts-analyser-result></ts-analyser-result>
      </div>
      <div v-else v-show="expanded" class="text-center">
        <div class="my-6 text-center">
          <v-img
            class="mx-auto mb-2"
            src="/dist/no_analyzer_results.png"
            alt="No analyzer results yet"
            max-width="200"
            contain
          ></v-img>
          <span>No analyzers run, yet.</span>
        </div>
        <v-btn
          :to="{ name: 'Analyze', params: { sketchId: sketch.id } }"
          plain
          color="primary"
          small
          center
          text
          class="mb-3"
        >
          + Run Analyzer
        </v-btn>
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
      analyzerResults: [],
      expanded: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  created() {},
}
</script>
