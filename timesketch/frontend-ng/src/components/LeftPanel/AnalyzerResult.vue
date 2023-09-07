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
    <!-- TODO: issue #2565 -->
    <!-- https://github.com/google/timesketch/issues/2565 -->
    <v-row
      no-gutters
      class="pa-3 pl-1"
      style="cursor: pointer"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <v-col cols="1" class="pl-1">
        <v-icon v-if="!expanded">mdi-chevron-right</v-icon>
        <v-icon v-else>mdi-chevron-down</v-icon>
      </v-col>
      <v-col cols="10">
        <span style="font-size: 0.9em">
          {{ analyzer.data.analyzerInfo.display_name }}
        </span>
      </v-col>

      <v-col cols="1">
        <div v-if="isActive" class="ml-1">
          <v-progress-circular
            :size="20"
            :width="1"
            indeterminate
          >
            <small>{{ Object.keys(analyzer.data.timelines).length }}</small>
          </v-progress-circular>
        </div>
        <div v-else class="ml-3">
          <small>{{ Object.keys(analyzer.data.timelines).length }}</small>
        </div>
      </v-col>
    </v-row>

    <v-expand-transition>
      <div v-show="expanded">
        <span
          style="font-size: 0.9em"
          v-for="timeline in analyzer.data.timelines"
          :key="timeline.id"
        >
          <ts-analyzer-result-timeline :timeline="timeline" :isMultiAnalyzer="analyzer.data.analyzerInfo.is_multi"></ts-analyzer-result-timeline>
        </span>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import TsAnalyzerResultTimeline from './AnalyzerResultTimeline.vue'

export default {
  props: ['analyzer','isActive'],
  components: {
    TsAnalyzerResultTimeline,
  },
  data: function () {
    return {
      expanded: false,
    }
  },
}
</script>
