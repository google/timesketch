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
  <v-expansion-panels accordion multiple v-model="panels">
    <v-expansion-panel key="0">
      <v-expansion-panel-header 
        v-slot="{ open }"
      >
        <v-row no-gutters>
          <v-col cols="4">
            Timelines
          </v-col>
          <v-col cols="8" class="text--secondary">
            <v-fade-transition leave-absolute>
              <span 
                v-if="open"
                key="timeline-name"
              >
                Select timelines by name.
              </span>
              <v-row 
                v-else 
                key="timeline-name"
                no-gutters 
                style="width: 100%"
              >
                <v-col cols="12">
                  {{ selectedTimelineIDs.length }} timeline(s) selected
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <TsTimelineSelectTable
          :selectedTimelineIDs="selectedTimelineIDs"
          @change="selectedTimelineIDs = $event"
        ></TsTimelineSelectTable>
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel key="1">
      <v-expansion-panel-header 
        v-slot="{ open }"
      >
        <v-row no-gutters>
          <v-col cols="4">
            Date/Time Range (optional)
          </v-col>
          <v-col cols="8" class="text--secondary">
            <v-fade-transition leave-absolute>
              <span 
                v-if="open"
                key="date-range"
              >
                Select a date range.
              </span>
              <v-row 
                v-else 
                key="date-range"
                no-gutters 
                style="width: 100%"
              >
                <v-col 
                  v-if="selectedDateRange.start != ''" 
                  cols="12"
                >
                  {{ selectedDateRange.start }} - {{ selectedDateRange.end }}
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
        </v-expansion-panel-header>
      <v-expansion-panel-content>
        <TsDateRangeSelect
          :range="selectedDateRange"
          @change="selectedDateRange = $event"
        ></TsDateRangeSelect>
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel key="2">
      <v-expansion-panel-header 
        v-slot="{ open }"
      >
        <v-row no-gutters>
          <v-col cols="4">
            Query string (optional)
          </v-col>
          <v-col cols="8" class="text--secondary">
            <v-fade-transition leave-absolute>
              <span 
                v-if="open"
              >
                Enter a query string.
              </span>
              <v-row 
                v-else 
                no-gutters 
                style="width: 100%"
              >
                <v-col 
                  v-if="selectedQueryString != ''" 
                  cols="12"
                >
                  {{ selectedQueryString }}
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <v-text-field
          v-model="selectedQueryString"
          outlined
          clearable
          :dense="isDense"
          label="Enter query string"
        >
        </v-text-field>
      </v-expansion-panel-content>
    </v-expansion-panel>
    <v-expansion-panel key="3">
      <v-expansion-panel-header 
        v-slot="{ open }"
      >
        <v-row no-gutters>
          <v-col cols="4">
            Date/Term/Label Filters
          </v-col>
          <v-col cols="8" class="text--secondary">
            <v-fade-transition leave-absolute>
              <span 
                v-if="open"
              >
                Add/remove filters.
              </span>
              <v-row 
                v-else 
                no-gutters 
                style="width: 100%"
              >
                <v-col cols="12">
                  {{ selectedBooleanFilters.length }} filter(s)
                </v-col>
              </v-row>
            </v-fade-transition>
          </v-col>
        </v-row>
      </v-expansion-panel-header>
      <v-expansion-panel-content>
        <TsBooleanFilterList
          :selectedQueryChips="selectedBooleanFilters"
          @change="selectedBooleanFilters = $event"
        >
        </TsBooleanFilterList>
      </v-expansion-panel-content>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script>
import TsTimelineSelectTable from './TimelineSelectTable.vue'
import TsDateRangeSelect from './DateRangeSelect.vue'
import TsBooleanFilterList from './BooleanFilterList.vue'

export default {
  components: {
    TsBooleanFilterList,
    TsDateRangeSelect,
    TsTimelineSelectTable,
  },
  props: {
    endDate: { 
      type: String, 
      default: '',
    },
    expandAll: { 
      type: Boolean, 
      default: true,
    },
    filterChips: { 
      type: Array, 
      default: function() { 
        return [] 
      },
    },
    isDense: { 
      type: Boolean, 
      default: false,
    },
    queryString: { 
      type: String, 
      default: '',
    },
    startDate: { 
      type: String, 
      default: '',
    },
    timelineIDs: { 
      type: Array, 
      default: function() { 
        return [1] 
      }, 
    },
  },
  data() {
    return {
      panels: this.openPanels(),
      selectedBooleanFilters: this.filterChips,
      selectedDateRange: {
        start: this.startDate,
        end: this.endDate,
      },
      selectedQueryString: this.queryString,
      selectedTimelineIDs: this.timelineIDs,
    }
  },
  methods: {
    openPanels() {
      if (this.expandAll) {
        return [...Array(4).keys()].map((k, i) => i)
      } else {
        return []
      }
    },
  },
  watch: {
    endDate() {
      this.selectedDateRange.end = this.endDate
    },
    filterChips() {
      this.selectedBooleanFilters = this.filterChips
    },
    queryString() {
      this.selectedQueryString = this.queryString
    },
    selectedBooleanFilters() {
      this.$emit('updateFilterChips', this.selectedBooleanFilters)
    },
    selectedDateRange() {
      this.$emit('updateFilterDateRange', this.selectedDateRange)
    },
    selectedQueryString() {
      this.$emit('updateFilterQueryString', this.selectedQueryString)
    },
    selectedTimelineIDs() {
      this.$emit('updateFilterTimelineIDs', this.selectedTimelineIDs)
    },
    startDate() {
      this.selectedDateRange.start = this.startDate
    },
    timelineIDs() {
      this.selectedTimelineIDs = this.timelineIDs
    },
  }
}
</script>
