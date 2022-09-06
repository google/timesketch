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
    <v-simple-table>
      <template v-slot:default>
        <thead>
          <tr>
            <th class="text-left">Name</th>
            <th class="text-left">Status</th>
            <th class="text-left">Events</th>
            <th class="text-left">Uploaded by</th>
            <th class="text-left">Created</th>
          </tr>
        </thead>
        <tbody>
          <ts-timeline-event :timeline="timeline" v-for="timeline in activeTimelines" :key="timeline.id" />
        </tbody>
      </template>
    </v-simple-table>
  </div>
</template>

<script>
import TsTimelineEvent from './TimelineEvent'

export default {
  components: {
    TsTimelineEvent,
  },
  props: [],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    activeTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.timelines]
      return timelines.sort(function (a, b) {
        return a.name.localeCompare(b.name)
      })
    },
  },
  data() {
    return {}
  },
  methods: {},
}
</script>
