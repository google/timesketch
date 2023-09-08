
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
    <div class="pa-4"
         :style="'cursor: pointer'"
         @click="expanded = !expanded"
         :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
      <span> <v-icon left>mdi-timeline-clock-outline</v-icon> Timelines </span>
      <ts-upload-timeline-form v-if="expanded"
                               btn-type="small"></ts-upload-timeline-form>
      <span class="float-right"
            style="margin-right: 10px">
        <small class="ml-3"><strong>{{ allTimelines.length }}</strong></small>
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <ts-timeline-chip v-for="timeline in allTimelines"
                          :key="timeline.id + timeline.name"
                          :timeline="timeline"></ts-timeline-chip>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import TsUploadTimelineForm from '../UploadForm'
import TsTimelineChip from '../Explore/TimelineChip'
export default {
  props: [],
  components: {
    TsUploadTimelineForm,
    TsTimelineChip,
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    allTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.timelines]
      timelines.sort(function (a, b) {
        return a.name.localeCompare(b.name)
      })
      return timelines
    },

  },
  data: function () {
    return {
      expanded: false,
    }
  },
}
</script>
