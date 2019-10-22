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
    <ts-sketch-explore-timeline-picker-item
      v-for="timeline in sketch.active_timelines"
      :key="timeline.id"
      :timeline="timeline"
      style="margin-right:7px;">
    </ts-sketch-explore-timeline-picker-item>
    <button class="button is-text" v-on:click="enableAllIndices">Enable all</button>
    <button class="button is-text" v-on:click="disableAllIndices">Disable all</button>
  </div>
</template>

<script>
import TsSketchExploreTimelinePickerItem from './TimelinePickerItem'

export default {
  components: {TsSketchExploreTimelinePickerItem},
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    },
    currentQueryFilter: {
      get: function () {
        return this.$store.state.currentQueryFilter
      },
      set: function (queryFilter) {
        this.$store.commit('updateCurrentQueryFilter', queryFilter)
      }
    },
  },
  methods: {
    enableAllIndices: function () {
      let allIndices = []
      this.sketch.active_timelines.forEach(function (timeline) {
        allIndices.push(timeline.searchindex.index_name)
      })
      this.currentQueryFilter.indices = allIndices
      this.$store.commit('search', this.sketch.id)
    },
    disableAllIndices: function () {
      this.currentQueryFilter.indices = []
      this.$store.commit('search', this.sketch.id)
    }
  },
  created: function () {
    if (this.currentQueryFilter.indices.includes('_all')) {
      this.enableAllIndices()
    }
  }
}
</script>
