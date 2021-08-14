<!--
Copyright 2019 Google Inc. All rights reserved.

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
  <ul class="content-list">
    <li style="padding:10px;" v-for="timeline in timelineList" :key="timeline.id">
      <ts-timeline-list-item
        :timeline="timeline"
        :controls="controls"
        :is-compact="isCompact"
        @remove="remove(timeline)"
        @save="save(timeline)"
      ></ts-timeline-list-item>
    </li>
    <li v-if="timelines.length > 9" style="padding:10px; cursor:pointer;">
      <span v-if="!showAllTimelines" v-on:click="showAllTimelines = true"
        >Show more ({{ sketch.timelines.length - 10 }})</span
      >
      <span v-if="showAllTimelines" v-on:click="showAllTimelines = false">Show less</span>
    </li>
  </ul>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsTimelineListItem from './TimelineListItem'

export default {
  components: { TsTimelineListItem },
  props: ['timelines', 'controls', 'isCompact'],
  data() {
    return {
      showAllTimelines: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    timelineList() {
      let timelines = [...this.timelines]
      if (this.showAllTimelines) {
        return timelines.reverse()
      }
      if (this.isCompact && this.timelines.length > 9) {
        return timelines.reverse().slice(0, 10)
      } else {
        return timelines.reverse()
      }
    },
  },
  methods: {
    remove(timeline) {
      ApiClient.deleteSketchTimeline(this.sketch.id, timeline.id)
        .then(response => {
          this.$store.dispatch('updateSketch', this.sketch.id)
        })
        .catch(e => {
          console.error(e)
        })
    },
    save(timeline) {
      ApiClient.saveSketchTimeline(this.sketch.id, timeline.id, timeline.name, timeline.description, timeline.color)
        .then(response => {
          this.$store.dispatch('updateSketch', this.sketch.id)
        })
        .catch(e => {
          console.error(e)
        })
    },
  },
}
</script>
