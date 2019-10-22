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
  <span class="tag is-medium" style="cursor: pointer;" v-bind:style="timelineColor" v-on:click="updateFilter">{{ timeline.name }}</span>
</template>

<script>
export default {
  props: ['timeline'],
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    currentQueryFilter: {
      get: function () {
        return this.$store.state.currentQueryFilter
      },
      set: function (queryFilter) {
        this.$store.commit('updateCurrentQueryFilter', queryFilter)
      }
    },
    timelineColor () {
      let indexName = this.timeline.searchindex.index_name
      let color = this.timeline.color
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
    }
  },
  methods: {
    toggleIndex: function (indexName) {
      let newArray = this.currentQueryFilter.indices.slice()
      let index = newArray.indexOf(indexName)
      if (index === -1) {
        newArray.push(indexName)
      } else {
        newArray.splice(index, 1)
      }
      return newArray
    },
    updateFilter: function () {
      let indexName = this.timeline.searchindex.index_name
      this.currentQueryFilter.indices = this.toggleIndex(indexName)
      this.$store.commit('search', this.sketch.id)
    }
  }
}
</script>
