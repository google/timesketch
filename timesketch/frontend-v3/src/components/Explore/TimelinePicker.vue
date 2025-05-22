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
  <span class="ml-3">
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
      size="small"
      variant="text"
      color="primary"
      v-if="sketch.timelines.length > 20"
      @click="showAll = !showAll"
      class="mr-5"
    >
      <span v-if="showAll"> show less </span>
      <span v-else> {{ sketch.timelines.length - 20 }} more.. </span>
    </v-btn>
    <br />
  </span>
</template>

<script>
import ApiClient from "@/utils/RestApiClient.js";
import EventBus from "@/event-bus.js";
import { useAppStore } from "@/stores/app";

import TsTimelineChip from './TimelineChip.vue'

import _ from 'lodash'

export default {
  components: { TsTimelineChip },
  props: ['currentQueryFilter', 'countPerIndex', 'countPerTimeline'],
  data() {
    return {
      appStore: useAppStore(),
      isDarkTheme: false,
      isLoading: false,
      showAll: false,
    }
  },
  computed: {
    sketch() {
      return this.appStore.sketch
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
  methods: {
    isSelected(timeline) {
      return this.appStore.enabledTimelines.includes(timeline.id)
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
          this.appStore.updateSketch(this.sketch.id).then(() => {
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
          this.appStore.updateSketch(this.sketch.id).then(() => {
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
      this.appStore.updateEnabledTimelines([timeline.id])
    },
    toggleTimeline(timeline) {
      this.appStore.toggleEnabledTimeline(timeline.id)
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
      if (!_.isEqual(newTimelineIds, this.appStore.enabledTimelines)) {
        this.appStore.updateEnabledTimelines(newTimelineIds)
      }
    },
  },
  created() {
    EventBus.$on('isDarkTheme', this.toggleTheme)
    // This was added during the migration to Pinia.
    this.appStore.updateEnabledTimelines(this.allTimelines.map((tl) => tl.id))
  },
  watch: {
    'currentQueryFilter.indices': {
      handler() {
        this.syncSelectedTimelines()
      },
      deep: true,
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.timeline-chip {
  display: inline-block;
}
</style>
