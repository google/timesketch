<!--
Copyright 2023 Google Inc. All rights reserved.

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
  <v-container class='ma-0'>
    <v-row class="mt-3">
      <v-col >
        <!-- <v-container class="ma-0"> -->
          <ts-timeline-search
            componentName="visualization"
            :analyzer-timeline-id="timelineIDs"
            @selectedTimelines="selectedTimelineIDs = $event"
          >
          </ts-timeline-search>
        <!-- </v-container> -->
      </v-col>
    </v-row>
    <v-row class="mt-n10">
      <v-col>
        <v-text-field
          outlined
          autofocus
          label="Event query"
          v-model="selectedQueryString"
        >
        </v-text-field>
      </v-col>
    </v-row>
    <v-row class="mt-n10">
      <v-col>
        <v-select
          v-bind="$attrs"
          v-model="selectedRecentSearch"
          :items="allRecentSearches"
          clearable
          solo
          dense
          label="Recent search"
          :disabled="!!selectedSavedSearch"
        >
        </v-select>
      </v-col>
      <v-col>
        <v-select
          v-bind="$attrs"
          v-model="selectedSavedSearch"
          :items="allSavedSearches"
          clearable
          solo
          dense
          label="Saved search"
          :disabled="!!selectedRecentSearch"
        >
        </v-select>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import TsTimelineSearch from '../Analyzer/TimelineSearch.vue'

export default {
  components: {
    TsTimelineSearch,
  },
  props: {
    queryString: {
      type: String
    },
    queryChips: {
      type: Array
    },
    recentSearch: {
      type: Object,
    },
    timelineIDs: {
      type: Array,
      default: function() {
        return []
      },
    },
  },
  data() {
    return {
      selectedFilter: '',
      selectedRecentSearch: null,
      selectedSavedSearch: null,
      selectedTimelineIDs: this.timelineIDs,
      selectedQueryString: this.queryString,
      selectedQueryChips: this.queryChips
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    allReadyTimelines() {
      // Sort alphabetically based on timeline name.
      const timelines = this.sketch.timelines.filter(
        tl => tl.status[0].status === 'ready'
      );
      timelines.sort((a, b) => a.name.localeCompare(b.name))
      return timelines;
    },
    allRecentSearches() {
      let searchHistory = this.$store.state.searchHistory
      if (Array.isArray(searchHistory)) {
        let recentSearches = this.$store.state.searchHistory.map(
          (view) => {
            return {
              text: `${view['query_string']} (${view['query_result_count']})`,
              value: view
            }
          }
        )
        return recentSearches
      }
      return []
    },
    allSavedSearches() {
      let savedSearches = this.$store.state.meta.views.map(
        (view) => {
          return {
            text: view['name'], value: view
          }
        }
      )
      return savedSearches
    }
  },
  watch: {
    queryString() {
      console.log(this.queryString)
      if (this.queryString) {
        return
      }
      this.selectedRecentSearch = null
      this.selectedSavedSearch = null
    },
    selectedSavedSearch() {
      if (!this.selectedSavedSearch) {
        this.selectedQueryString = ''
        this.selectedTimelineIDs = []
        this.selectedQueryChips = null
      } else {
        this.selectedQueryString = this.selectedSavedSearch.query
        let queryFilter = JSON.parse(this.selectedSavedSearch.filter)

        let indices = queryFilter.indices
        if (indices === '_all') {
          this.selectedTimelineIDs = this.allReadyTimelines.map((x) => x.id)
        } else {
          this.selectedTimelineIDs = indices
        }

        this.selectedQueryChips = queryFilter.chips.filter(
          (chip) => chip.type === 'label' || chip.type === 'term' || chip.type === 'datetime_range'
        );
      }
    },
    selectedRecentSearch() {
      if (!this.selectedRecentSearch) {
        this.selectedQueryString = ''
        this.selectedTimelineIDs = []
        this.selectedQueryChips = null
      } else {
        this.selectedQueryString = this.selectedRecentSearch.query_string
        let queryFilter = JSON.parse(this.selectedRecentSearch.query_filter)
        let indices = queryFilter.indices
        if (indices === '_all') {
          this.selectedTimelineIDs = this.allReadyTimelines.map((x) => x.id)
        } else {
          this.selectedTimelineIDs = indices
        }

        this.selectedQueryChips = queryFilter.chips.filter(
          (chip) => chip.type === 'label' || chip.type === 'term' || chip.type === 'datetime_range'
        );
      }
    },
    selectedTimelineIDs() {
      this.$emit('updateTimelineIDs', this.selectedTimelineIDs)
    },
    selectedQueryString() {
      this.$emit('updateQueryString', this.selectedQueryString)
    },
    selectedQueryChips() {
      this.$emit('updateQueryChips', this.selectedQueryChips)
    }
  }
}
</script>
