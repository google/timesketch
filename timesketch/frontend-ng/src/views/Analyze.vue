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
  <v-container fluid>

    <!-- Search and Filters -->
    <v-card flat class="pa-3 pt-0 mt-n3" color="transparent">
      <v-card class="d-flex align-start mb-1" outlined>
        <div>
          &gt;&gt; Run analyzer search belongs here!

        </div>
        </v-card>
        <v-btn
            :to="{ name: 'Overview', params: { sketchId: sketchId } }"
            color="primary"
            depressed
            text
            class="mt-1"
          >
            &lt;&lt; back to explore
          </v-btn>
    </v-card>
  </v-container>
</template>

<script>

  import { None } from 'vega'

  import { dragscroll } from 'vue-dragscroll'

  const defaultQueryFilter = () => {
    return {
      from: 0,
      terminate_after: 40,
      size: 40,
      indices: [],
      order: 'asc',
      chips: [],
    }
  }

  export default {
    directives: {
      dragscroll,
    },
    components: {

    },
    props: ['sketchId'],
    data() {
      return {
        columnHeaders: [
          {
            text: '',
            value: 'field',
          },
        ],
        tableOptions: {
          itemsPerPage: 40,
        },
        currentItemsPerPage: 40,
        drawer: false,
        leftDrawer: true,
        expandedRows: [],
        timeFilterMenu: false,
        selectedFields: [{ field: 'message', type: 'text' }],
        searchColumns: '',
        columnDialog: false,
        saveSearchMenu: false,
        saveSearchFormName: '',
        selectedEventTags: [],
        showRightSidePanel: false,
        addManualEvent: false,
        datetimeManualEvent: '', // datetime of an event used
        // TODO: Refactor this into a configurable option
        // Issue: https://github.com/google/timesketch/issues/2339
        tagConfig: {
          good: { color: 'green', textColor: 'white', label: 'mdi-check-circle-outline' },
          bad: { color: 'red', textColor: 'white', label: 'mdi-alert-circle-outline' },
          suspicious: { color: 'orange', textColor: 'white', label: 'mdi-help-circle-outline' },
        },

        // old stuff
        params: {},
        searchInProgress: false,
        currentPage: 1,
        contextEvent: false,
        originalContext: false,
        showSearchDropdown: false,
        eventList: {
          meta: {},
          objects: [],
        },
        currentQueryString: '',
        currentQueryFilter: defaultQueryFilter(),
        selectedEvents: [],
        displayOptions: {
          isCompact: false,
          showTags: true,
          showEmojis: true,
          showMillis: false,
          showTimelineName: true,
        },
        selectedLabels: [],
        showSearchHistory: false,
        showHistogram: false,
        branchParent: None,
        zoomLevel: 0.7,
        zoomOrigin: {
          x: 0,
          y: 0,
        },
        minimizeRightSidePanel: false,
      }
    },
    computed: {
      sketch() {
        return this.$store.state.sketch
      },
      meta() {
        return this.$store.state.meta
      },
      totalHits() {
        return this.eventList.meta.es_total_count_complete || 0
      },
      totalTime() {
        return this.eventList.meta.es_time / 1000 || 0
      },
      fromEvent() {
        return this.currentQueryFilter.from || 1
      },
      toEvent() {
        if (this.totalHits < this.currentQueryFilter.size) {
          return
        }
        return parseInt(this.currentQueryFilter.from) + parseInt(this.currentQueryFilter.size)
      },
      numSelectedEvents() {
        return this.selectedEvents.length
      },
      filterChips: function () {
        return this.currentQueryFilter.chips.filter((chip) => chip.type === 'label' || chip.type === 'term')
      },
      timeFilterChips: function () {
        return this.currentQueryFilter.chips.filter((chip) => chip.type.startsWith('datetime'))
      },
      filteredLabels() {
        return this.$store.state.meta.filter_labels.filter((label) => !label.label.startsWith('__'))
      },
      currentSearchNode() {
        return this.$store.state.currentSearchNode
      },
    },
    methods: {

    },

    watch: {

    },
    mounted() {

    },
    beforeDestroy() {

    },
    created: function () {

    },
  }
  </script>
