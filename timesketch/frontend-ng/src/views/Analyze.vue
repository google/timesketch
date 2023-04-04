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
    <v-card flat class="pa-3 pt-0 mt-n3" color="transparent">
      <div class="mt-2">
        <ts-timeline-search :analyzer-timeline-id="analyzerTimelineId" @selectedTimelines="timelineSelection = $event"></ts-timeline-search>
      </div>
      <v-divider></v-divider>
      <div>
        <ts-analyzer-list :timelineSelection="timelineSelection"></ts-analyzer-list>
      </div>
      <v-divider></v-divider>
    </v-card>
  </v-container>
</template>

<script>
import TsTimelineSearch from '../components/Analyzer/TimelineSearch'
import TsAnalyzerList from '../components/Analyzer/AnalyzerList'

export default {
  components: {
    TsTimelineSearch,
    TsAnalyzerList,
  },
  props: ['sketchId', 'analyzerTimelineId'],
  data() {
    return {
      timelineSelection: [],
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
}
</script>
