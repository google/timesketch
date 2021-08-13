<!--
Copyright 2021 Google Inc. All rights reserved.

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
    <b-loading :is-full-page="false" v-model="isLoading" :can-cancel="false">
      <div class="lds-ripple">
        <div></div>
        <div></div>
      </div>
      <div style="position: absolute; margin-top:120px;">
        <b>Reloading timelines</b>
      </div>
    </b-loading>
    <ts-timeline-chip
      v-for="timeline in activeTimelines"
      :key="timeline.id + timeline.name"
      :timeline="timeline"
      :is-selected="isSelected(timeline)"
      :is-empty-state="isEmptyState"
      :events-count="getCount(timeline)"
      @remove="remove"
      @save="save"
      @toggle="toggleTimeline"
    ></ts-timeline-chip>
    <div v-if="activeTimelines.length > 3" style="margin-top:7px;">
      <span style="text-decoration: underline; cursor: pointer; margin-right: 10px;" v-on:click="enableAllTimelines"
        >Enable all
      </span>
      <span style="text-decoration: underline; cursor: pointer;" v-on:click="disableAllTimelines">Disable all </span>
    </div>
  </div>
</template>

<script>
import EventBus from '../../main'
import TsTimelineChip from './TimelineChip'
import ApiClient from '../../utils/RestApiClient'

export default {
  components: { TsTimelineChip },
  props: ['currentQueryFilter', 'countPerIndex', 'countPerTimeline'],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    activeTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.active_timelines]
      return timelines.sort(function(a, b) {
        return a.name.localeCompare(b.name)
      })
    },
    isEmptyState() {
      return this.countPerTimeline === undefined
    },
  },
  data() {
    return {
      isDarkTheme: false,
      isLoading: false,
      selectedTimelines: [],
    }
  },
  methods: {
    isSelected(timeline) {
      return this.selectedTimelines.includes(timeline)
    },
    getCount(timeline) {
      let count = 0
      if (this.countPerTimeline) {
        count = this.countPerTimeline[timeline.id]
        if (typeof count === 'number') {
          return count
        }
      }
      // Support for old style indices
      if (!count && this.countPerIndex) {
        count = this.countPerIndex[timeline.searchindex.index_name]
      }
      return count
    },
    remove(timeline) {
      this.isLoading = true
      ApiClient.deleteSketchTimeline(this.sketch.id, timeline.id)
        .then(() => {
          this.$store.dispatch('updateSketch', this.sketch.id).then(() => {
            this.syncSelectedTimelines()
            this.isLoading = false
          })
        })
        .catch(e => {
          console.error(e)
          this.isLoading = false
        })
    },
    save(timeline, newTimelineName = false) {
      // Only show the progress bar if renaming the timeline
      if (newTimelineName) {
        this.isLoading = true
      }
      ApiClient.saveSketchTimeline(
        this.sketch.id,
        timeline.id,
        newTimelineName || timeline.name,
        timeline.description,
        timeline.color
      )
        .then(() => {
          this.$store.dispatch('updateSketch', this.sketch.id).then(() => {
            this.syncSelectedTimelines()
            this.isLoading = false
          })
        })
        .catch(e => {
          console.error(e)
          this.isLoading = false
        })
    },
    enableAllTimelines() {
      this.selectedTimelines = this.activeTimelines
      this.$emit('updateSelectedTimelines', this.selectedTimelines)
    },
    disableAllTimelines() {
      this.selectedTimelines = []
      this.$emit('updateSelectedTimelines', this.selectedTimelines)
    },
    toggleTimeline(timeline) {
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
    toggleTheme() {
      this.isDarkTheme = !this.isDarkTheme
    },
    syncSelectedTimelines() {
      if (this.currentQueryFilter.indices.includes('_all')) {
        this.selectedTimelines = this.activeTimelines
        return
      }
      let newArray = []
      this.currentQueryFilter.indices.forEach(index => {
        if (typeof index === 'string') {
          let timeline = this.activeTimelines.find(t => {
            return t.searchindex.index_name === index
          })
          newArray.push(timeline)
        } else if (typeof index === 'number') {
          let timeline = this.activeTimelines.find(t => {
            return t.id === index
          })
          newArray.push(timeline)
        }
      })
      this.selectedTimelines = newArray
    },
  },
  created() {
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
