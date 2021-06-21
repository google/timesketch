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
  <div>
    <!-- TODO(bartoszi): Confirm if these are still required -->
    <!-- :is-compact="isCompact" -->
    <!-- :controls="controls" -->
    <ts-timeline-chip
      v-for="timeline in activeTimelines"
      :key="timeline.id"
      :timeline="timeline"
      :selectedTimelines="selectedTimelines"
      :countPerIndex="countPerIndex"
      :countPerTimeline="countPerTimeline"
      @remove="remove(timeline)"
      @save="save(timeline)"
      @toggle="toggleTimeline(timeline)"
    ></ts-timeline-chip>
    <!-- <ts-timeline-chip
      v-for="timeline in activeTimelines"
      :key="timeline.id"
          :timeline="timeline"
      class="tag is-medium has-text-left"
          style="cursor:pointer; margin-right:7px; margin-bottom:7px; padding-right:6px;"
      v-bind:style="timelineColor(timeline)"
      v-on:click="toggleTimeline(timeline)"
        ></ts-timeline-chip> -->
    <div v-if="activeTimelines.length > 3" style="margin-top:7px;">
      <span style="text-decoration: underline; cursor: pointer; margin-right: 10px;" v-on:click="enableAllTimelines"
        >Enable all</span
      >
      <span style="text-decoration: underline; cursor: pointer;" v-on:click="disableAllTimelines">Disable all</span>
    </div>
  </div>
</template>

<script>
import EventBus from '../../main'
import TsTimelineChip from './TimelineChip'
import ApiClient from '../../utils/RestApiClient'

export default {
  components: { TsTimelineChip },
  props: ['activeTimelines', 'currentQueryFilter', 'countPerIndex', 'countPerTimeline'],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  data() {
    return {
      isDarkTheme: false,
      selectedTimelines: [],
      timelineCount: {},
    }
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
      this.syncSelectedTimelines()
    },
    enableAllTimelines: function() {
      this.selectedTimelines = this.activeTimelines
      this.$emit('updateSelectedTimelines', this.selectedTimelines)
    },
    disableAllTimelines: function() {
      this.selectedTimelines = []
      this.$emit('updateSelectedTimelines', this.selectedTimelines)
    },
    toggleTimeline: function(timeline) {
      let newArray = this.selectedTimelines.slice()
      let timelineIdx = newArray.indexOf(timeline)
      if (timelineIdx === -1) {
        newArray.push(timeline)
      } else {
        newArray.splice(timelineIdx, 1)
      }
      this.selectedTimelines = newArray
      this.$emit('updateSelectedTimelines', this.selectedTimelines)
    },
    toggleTheme: function() {
      this.isDarkTheme = !this.isDarkTheme
    },
    syncSelectedTimelines: function() {
      let timelines = []
      this.currentQueryFilter.indices.forEach(index => {
        if (typeof index === 'string') {
          let timeline = this.activeTimelines.find(timeline => {
            return timeline.searchindex.index_name === index
          })
          timelines.push(timeline)
        } else if (typeof index === 'number') {
          let timeline = this.activeTimelines.find(timeline => {
            return timeline.id === index
          })
          timelines.push(timeline)
        }
      })
      this.selectedTimelines = timelines
    },
  },
  created: function() {
    EventBus.$on('isDarkTheme', this.toggleTheme)
    EventBus.$on('clearSearch', this.enableAllTimelines)

    if (this.currentQueryFilter.indices.includes('_all')) {
      this.selectedTimelines = this.activeTimelines
    } else {
      this.syncSelectedTimelines()
    }
  },
  watch: {
    'currentQueryFilter.indices'(val) {
      this.syncSelectedTimelines()
    },
    deep: true,
  },
}
</script>
