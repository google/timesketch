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
      :style="!(sketchAnalysesList.length) ? '' : 'cursor: pointer'"
      flat
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span>
        <v-icon left>mdi-auto-fix</v-icon> Analyzer Results
      </span>
      <v-btn
        v-if="expanded || !(sketchAnalysesList.length)"
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
        <small><strong>{{ sketchAnalysesList.length }}</strong></small>
      </span>

    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <div v-if="sketchAnalysesList.length > 0">
          <!-- TODO: issue#2565 -->
          <!-- Add a severity and timeline filter here. -->
          <v-data-iterator :items="sketchAnalysesList" hide-default-footer>
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
// import RestApiClient from '../../utils/RestApiClient'
import TsAnalyserResult from './AnalyzerResult.vue'

export default {
  props: [],
  components: {
    TsAnalyserResult,
  },
  data: function () {
    return {
      expanded: false,
      analyses: [],
      analyzerList: {},
    }
  },
  methods: {
    // TODO: Have an automatic poll for new analyzers running when they are triggered.
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    sketchAnalyzerList() {
      return this.$store.state.sketchAnalyzerList
    },
    sketchAnalysesList() {
      return this.$store.state.sketchAnalysesList
    },
  },
  created() {
  },
}
</script>
