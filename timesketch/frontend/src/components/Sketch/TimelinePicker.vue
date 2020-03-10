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
    <span v-for="timeline in sketch.active_timelines" :key="timeline.id" class="tag is-medium" style="cursor: pointer; margin-right: 7px;margin-bottom:7px;" v-bind:style="timelineColor(timeline)" v-on:click="toggleIndex(timeline.searchindex.index_name)">
      {{ timeline.name }} <span v-if="indexIsEnabled(timeline.searchindex.index_name)" class="tag is-small" style="margin-left:10px;margin-right:-7px;background-color: rgba(255,255,255,0.5);">{{ countPerIndex[timeline.searchindex.index_name] || '0' }}</span>
    </span>
    <div v-if="sketch.active_timelines.length > 3" style="margin-top:7px;">
      <span style="text-decoration: underline; cursor: pointer; margin-right: 10px;" v-on:click="enableAllIndices">Enable all</span>
      <span style="text-decoration: underline; cursor: pointer;" v-on:click="disableAllIndices">Disable all</span>
    </div>
  </div>
</template>

<script>
export default {
  props: ['currentQueryFilter', 'countPerIndex'],
  computed: {
    sketch () {
      return this.$store.state.sketch
    }
  },
  methods: {
    timelineColor (timeline) {
      let indexName = timeline.searchindex.index_name
      let color = timeline.color
      if (!color.startsWith('#')) {
        color = '#' + color
      }
      // Grey out the index if it is not selected.
      if (!this.currentQueryFilter.indices.includes(indexName)) {
        color = '#f5f5f5'
      }
      return {
        'background-color': color
      }
    },
    toggleIndex: function (indexName) {
      let newArray = this.currentQueryFilter.indices.slice()
      let index = newArray.indexOf(indexName)
      if (index === -1) {
        newArray.push(indexName)
      } else {
        newArray.splice(index, 1)
      }
      this.currentQueryFilter.indices = newArray
      this.$emit('updateQueryFilter', this.currentQueryFilter)
    },
    enableAllIndices: function () {
      let allIndices = []
      this.sketch.active_timelines.forEach(function (timeline) {
        allIndices.push(timeline.searchindex.index_name)
      })
      this.currentQueryFilter.indices = allIndices
      this.$emit('updateQueryFilter', this.currentQueryFilter)
    },
    disableAllIndices: function () {
      this.currentQueryFilter.indices = []
      this.$emit('updateQueryFilter', this.currentQueryFilter)
    },
    indexIsEnabled: function (index) {
      return this.currentQueryFilter.indices.includes(index)
    }
  },
  created: function () {
    if (this.currentQueryFilter.indices.includes('_all')) {
      let allIndices = []
      this.sketch.active_timelines.forEach(function (timeline) {
        allIndices.push(timeline.searchindex.index_name)
      })
      this.currentQueryFilter.indices = allIndices
    }
  }
}
</script>
