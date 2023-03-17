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
  <v-container fluid>
    <!-- Search and Filters -->
    <v-card flat class="pa-3 pt-0 mt-n3" color="transparent">
      <v-btn :to="{ name: 'Overview', params: { sketchId: sketchId } }" color="primary" plain text>
        &lt;&lt; back to explore
      </v-btn>
      <div>
        <ts-analyzer-search></ts-analyzer-search>

      </div>
      <v-divider></v-divider>
      <div>
        <!-- TODO: https://github.com/google/timesketch/issues/2562 -->
        TODO: <a href="https://github.com/google/timesketch/issues/2562">Issue#2562</a> add the analyzer listing
        component.
      </div>
      <v-divider></v-divider>
    </v-card>
  </v-container>
</template>

<script>
import TsAnalyzerSearch from '../components/Analyzer/AnalyzerSearch'

export default {
  directives: {},
  components: {
    TsAnalyzerSearch
  },
  props: ['sketchId'],
  data() {
    return {}
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  methods: {},
}
</script>
