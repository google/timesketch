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
  <span>
    <ts-timeline-chip
      v-for="timeline in allTimelines"
      class="mr-2 mb-3 timeline-chip"
      :key="timeline.id + timeline.name"
      :timeline="timeline"
      :is-selected="isSelected(timeline)"
      :is-empty-state="isEmptyState"
      :events-count="getCount(timeline)"
      @remove="remove"
      @save="save"
      @toggle="toggleTimeline"
      @disableAllOtherTimelines="disableAllOtherTimelines"
    ></ts-timeline-chip>
    <v-btn
      small
      text
      rounded
      color="primary"
      v-if="sketch.timelines.length > 20"
      @click="showAll = !showAll"
      class="mt-n3 mr-5"
    >
      <span v-if="showAll"> show less </span>
      <span v-else> {{ sketch.timelines.length - 20 }} more.. </span>
    </v-btn>
    <br />
  </span>
</template>

<script>
import EventBus from '../../event-bus.js'
import TsTimelineChip from './TimelineChip.vue'
import ApiClient from '../../utils/RestApiClient.js'

import _ from 'lodash'

export default {
  components: { TsTimelineChip },
  props: ['currentQueryFilter', 'countPerIndex', 'countPerTimeline'],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    allTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.timelines]
      timelines = timelines.sort(function (a, b) {
        return a.name.localeCompare(b.name)
      })
      if (!this.showAll) {
        timelines = timelines.slice(0, 20)
      }
      return timelines
    },
    activeTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.active_timelines]
      return timelines.sort(function (a, b) {
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
      showAll: false,
    }
  },
  methods: {
    isSelected(timeline) {
      return this.$store.state.enabledTimelines.includes(timeline.id)
    },
    getCount(timeline) {
      if (this.countPerTimeline) {
        const count = this.countPerTimeline[timeline.id]
        if (typeof count === 'number') {
          return count
        }
      }
      return 0
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
        .catch((e) => {
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
        .catch((e) => {
          console.error(e)
          this.isLoading = false
        })
    },
    disableAllOtherTimelines(timeline) {
      this.$store.dispatch('updateEnabledTimelines', [timeline.id])
    },
    toggleTimeline(timeline) {
      this.$store.dispatch('toggleEnabledTimeline', timeline.id)
    },
    toggleTheme() {
      this.isDarkTheme = !this.isDarkTheme
    },
    syncSelectedTimelines() {
      if (this.currentQueryFilter.indices.includes('_all')) {
        this.updateEnabledTimelinesIfChanged(this.activeTimelines.map((tl) => tl.id))
        return
      }
      let newArray = []
      this.currentQueryFilter.indices.forEach((index) => {
        if (typeof index === 'string') {
          let timeline = this.activeTimelines.find((t) => {
            return t.searchindex.index_name === index
          })
          newArray.push(timeline)
        } else if (typeof index === 'number') {
          let timeline = this.activeTimelines.find((t) => {
            return t.id === index
          })
          newArray.push(timeline)
        }
      })
      this.updateEnabledTimelinesIfChanged(newArray.map((tl) => tl.id))
    },
    updateEnabledTimelinesIfChanged(newTimelineIds) {
      if (!_.isEqual(newTimelineIds, this.$store.state.enabledTimelines)) {
        this.$store.dispatch('updateEnabledTimelines', newTimelineIds)
      }
    },
  },
  created() {
    EventBus.$on('isDarkTheme', this.toggleTheme)
  },
  watch: {
    'currentQueryFilter.indices'(val) {
      this.syncSelectedTimelines()
    },
    deep: true,
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.timeline-chip {
  display: inline-block;
}
</style>
