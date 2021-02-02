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
    <span v-for="timeline in activeTimelines" :key="timeline.id" class="tag is-medium has-text-left" style="cursor: pointer; margin-right: 7px;margin-bottom:7px;" v-bind:style="timelineColor(timeline)" v-on:click="toggleTimeline(timeline)">
      {{ timeline.name }} <span class="tag is-small" style="margin-left:10px;margin-right:-7px;background-color: rgba(255,255,255,0.5);min-width:50px;"><span v-if="timelineIsEnabled(timeline) && countPerTimeline">{{ getCount(timeline) | compactNumber }}</span></span>
    </span>
    <div v-if="activeTimelines.length > 3" style="margin-top:7px;">
      <span style="text-decoration: underline; cursor: pointer; margin-right: 10px;" v-on:click="enableAllTimelines">Enable all</span>
      <span style="text-decoration: underline; cursor: pointer;" v-on:click="disableAllTimelines">Disable all</span>
    </div>
  </div>
</template>

<script>
import EventBus from "../../main"

export default {
  props: ['activeTimelines', 'currentQueryFilter', 'countPerIndex', 'countPerTimeline'],
  data () {
    return {
      isDarkTheme: false,
      selectedTimelines: [],
      timelineCount: {}
    }
  },
  methods: {
    timelineColor (timeline) {
      this.isDarkTheme = localStorage.theme === 'dark'
      let backgroundColor = timeline.color
      let textDecoration = 'none'
      let opacity = '100%'
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
      }
      // Grey out the index if it is not selected.
      if (!this.selectedTimelines.includes(timeline)) {
        backgroundColor = '#d2d2d2'
        textDecoration = 'line-through'
        opacity = '50%'
      }

      if (this.isDarkTheme) {
        return {
          'background-color': backgroundColor,
          'text-decoration': textDecoration,
          'opacity': opacity,
          'filter': 'grayscale(25%)',
          'color': '#333333'
        }
      }
      return {
        'background-color': backgroundColor,
        'text-decoration': textDecoration,
        'opacity': opacity,
      }
    },
    toggleTimeline: function (timeline) {
      let newArray = this.selectedTimelines.slice()
      let timeline_idx = newArray.indexOf(timeline)
      if (timeline_idx === -1) {
        newArray.push(timeline)
      } else {
        newArray.splice(timeline_idx, 1)
      }
      this.selectedTimelines = newArray
      this.$emit('updateSelectedTimelines', this.selectedTimelines)
    },
    enableAllTimelines: function () {
      this.selectedTimelines = this.activeTimelines
      this.$emit('updateSelectedTimelines', this.selectedTimelines)
    },
    disableAllTimelines: function () {
      this.selectedTimelines = []
      this.$emit('updateSelectedTimelines', this.selectedTimelines)
    },
    timelineIsEnabled: function (timeline) {
      return this.selectedTimelines.includes(timeline)
    },
    toggleTheme: function () {
      this.isDarkTheme =! this.isDarkTheme
    },
    getCount: function (timeline) {
      let count = this.countPerTimeline[timeline.id]
      // Support for old style indices
      if (count === undefined) {
        count = this.countPerIndex[timeline.searchindex.index_name]
      }
      return count
    },
    syncSelectedTimelines: function () {
      let timelines = []
      this.currentQueryFilter.indices.forEach((index) => {
        if (typeof(index) === 'string') {
          let timeline = this.activeTimelines.find((timeline) => {
            return timeline.searchindex.index_name === index
          })
          timelines.push(timeline)
        } else if (typeof(index) === 'number') {
          let timeline = this.activeTimelines.find((timeline) => {
            return timeline.id === index
          })
          timelines.push(timeline)
        }
      })
      this.selectedTimelines = timelines
    }
  },
  created: function () {
    EventBus.$on('isDarkTheme', this.toggleTheme)
    EventBus.$on('clearSearch', this.enableAllTimelines)

    if (this.currentQueryFilter.indices.includes('_all')) {
      this.selectedTimelines = this.activeTimelines
    } else {
      this.syncSelectedTimelines()
    }
  },
  watch: {
    "currentQueryFilter.indices" (val) {
      this.syncSelectedTimelines()
    }, deep: true
  }
}
</script>
