<!--
Copyright 2024 Google Inc. All rights reserved.

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
    <v-radio-group v-model="source" column>
      <v-radio label="New" value="new"></v-radio>
      <v-radio label="Current search parameters in explore view" value="current"></v-radio>
      <v-radio label="Saved search" value="saved"></v-radio>
    </v-radio-group>
    <v-autocomplete 
      v-if="source == 'saved'"
      v-model="selectedSavedSearch"
      :items="allSavedSearches"
      clearable
      outlined
      label="Select a saved search"
    >
    </v-autocomplete>
  </div>
</template>

<script>

export default {
  props: {

  },
  data() {
    return {
      selectedSavedSearch: undefined,
      source: null
    }
  },
  computed: {
    allSavedSearches() {
      let savedSearches = this.$store.state.meta.views.map(
        (view) => { return {text: view['name'], value: view} }
      )
      return savedSearches
    },
    allTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = this.sketch.timelines.map(
        (timeline) => { return {text: timeline['name'], value: timeline['id']} }
      )
      return timelines
    },
  },
  methods: {
    sourceUpdated() {
      if (this.source === 'new') {
        let queryParameters = {
          timelines: this.allTimelines,
          queryFilters: [],
          queryString: null,
          start: null,
          end: null,
        }
        this.$emit('changed', queryParameters)
      } else if (this.source === 'current') {
        let selectedTimelines = this.queryFilter.indices
        let queryString = this.currentSearchNode['query_string']
        let queryFilter = JSON.parse(this.$store.state.currentSearchNode['query_filter'])
        let queryChips = queryFilter.chips.filter(
          (chip) => chip.type === 'label' || chip.type === 'term' || chip.type === 'datetime_range'
        );
        let queryParameters = {
          timelines: selectedTimelines,
          queryFilters: queryChips,
          queryString: queryString,
          start: null,
          end: null,
        }
        this.$emit('changed', queryParameters)
      } else if (this.source === 'saved') {
        let selectedTimelines = this.queryFilter.indices
        let queryString = this.selectedSavedSearch.query
        let queryFilter = JSON.parse(this.selectedSavedSearch.filter)
        let queryChips = queryFilter.chips.filter(
          (chip) => chip.type === 'label' || chip.type === 'term' || chip.type === 'datetime_range'
        );
        let queryParameters = {
          timelines: selectedTimelines,
          queryFilters: queryChips,
          queryString: queryString,
          start: null,
          end: null,
        }
        this.$emit('changed', queryParameters)
      }
    },  
  }
}
</script>