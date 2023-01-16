<!--
Copyright 2022 Google Inc. All rights reserved.

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
    <div class="pa-4" flat :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
      <span style="cursor: pointer" @click="expanded = !expanded">
        <v-icon left>mdi-auto-fix</v-icon> Analyzer Results ({{ analyzerResults.length }})
      </span>
      <v-btn
        :to="{ name: 'Analyse', params: { sketchId: sketch.id } }"
        plain
        color="primary"
        x-small
        right
        absolute
        text
        class="mt-1"
        style="cursor: pointer"
      >
        + Run Analyzer
      </v-btn>
    </div>
    <v-expand-transition>
      <div v-if="analyzerResults.length > 0" v-show="expanded">
        Here are some results!
        <!-- <ts-analyser-result></ts-analyser-result> -->
      </div>
      <div v-else v-show="expanded">
        No results yet! Sketch: {{ sketch.id }}
        <v-img
          contain
          max-height=110
          max-width=280
          src="../../assets/no_analyzer_results.png"
        ></v-img>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
// import TsAnalyserResult from './AnalyzerResult.vue'

export default {
  props: [],
  components: {
    // TsAnalyserResult,
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
  created() {
  },
}
</script>
