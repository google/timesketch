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
    <span v-for="timeline in sketch.active_timelines" :key="timeline.id" class="tag is-medium has-text-left" style="cursor: pointer; margin-right: 7px;margin-bottom:7px;" v-bind:style="timelineColor(timeline)" v-on:click="toggleIndex(timeline.searchindex.index_name)">
      {{ timeline.name }} <span class="tag is-small" style="margin-left:10px;margin-right:-7px;background-color: rgba(255,255,255,0.5);min-width:50px;"><span v-if="indexIsEnabled(timeline.searchindex.index_name)">{{ countPerIndex[timeline.searchindex.index_name] | compactNumber }}</span></span>
    </span>
    <div v-if="sketch.active_timelines.length > 1" style="margin-top:7px;">
      <span style="text-decoration: underline; cursor: pointer; margin-right: 10px;" v-on:click="enableAllIndices">Enable all</span>
      <span style="text-decoration: underline; cursor: pointer;" v-on:click="disableAllIndices">Disable all</span>
    </div>
  </div>
</template>

<script>
import EventBus from "../../main"

export default {
  props: ['currentQueryFilter', 'countPerIndex'],
  data () {
    return {
      isDarkTheme: false,
      allTimelines: [],
      selectedTimelines: []
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    }
  },
  methods: {
    timelineColor (timeline) {
      this.isDarkTheme = localStorage.theme === 'dark'
      let indexName = timeline.searchindex.index_name
      let backgroundColor = timeline.color
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
      }
      // Grey out the index if it is not selected.
      if (!this.selectedTimelines.includes(indexName)) {
        backgroundColor = '#f5f5f5'
      }

      if (this.isDarkTheme) {
        return {
          'background-color': backgroundColor,
          'filter': 'grayscale(25%)',
          'color': '#333'
        }
      }
      return {
        'background-color': backgroundColor
      }
    },
    toggleIndex: function (indexName) {
      let newArray = this.selectedTimelines.slice()
      let index = newArray.indexOf(indexName)
      if (index === -1) {
        newArray.push(indexName)
      } else {
        newArray.splice(index, 1)
      }
      this.selectedTimelines = newArray
      this.$emit('updateSelectedIndices', this.selectedTimelines)
    },
    setAllIndices: function () {
      let allIndices = []
      this.sketch.active_timelines.forEach(function (timeline) {
        allIndices.push(timeline.searchindex.index_name)
      })
      this.selectedTimelines = allIndices
    },
    enableAllIndices: function () {
      this.setAllIndices()
      this.$emit('updateSelectedIndices', this.selectedTimelines)
    },
    disableAllIndices: function () {
      this.selectedTimelines = []
      this.$emit('updateSelectedIndices', this.selectedTimelines)
    },
    indexIsEnabled: function (index) {
      return this.selectedTimelines.includes(index)
    },
    toggleTheme: function () {
      this.isDarkTheme =! this.isDarkTheme
    }
  },
  created: function () {
    EventBus.$on('isDarkTheme', this.toggleTheme)
    EventBus.$on('clearSearch', this.enableAllIndices)

    let timelines = []
    this.sketch.active_timelines.forEach(function (timeline) {
      timelines.push(timeline.searchindex.index_name)
    })
    this.allTimelines = timelines

    if (this.currentQueryFilter.indices.includes('_all')) {
      this.selectedTimelines = this.allTimelines
    } else {
      this.selectedTimelines = this.currentQueryFilter.indices
    }
  }
}
</script>
