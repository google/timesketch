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
  <v-card outlined>
    <v-card-title>
      Create new visualization
    </v-card-title>
    <v-card-text>
      <v-stepper v-model="currentStep" vertical flat>
        <v-stepper-step step="1" editable>
          Aggregation Type
          <small>Select and configure event aggregation</small>
        </v-stepper-step>
        <v-stepper-content step="1">
          <v-card outlined>
            <v-card-text>
              <TsAggregationSelect
                v-bind:field="selectedField"
                @updateField="selectedField = $event"
                v-bind:aggregator="selectedAggregator"
                @updateAggregator="selectedAggregator = $event"
                v-bind:metric="selectedMetric"
                @updateMetric="selectedMetric = $event"
                v-bind:maxItems="selectedMaxItems"
                @updateMaxItems="selectedMaxItems = $event"
                v-bind:interval="selectedInterval"
                @updateInterval="selectedInterval = $event"
                v-bind:intervalQuantity="selectedIntervalQuantity"
                @updateIntervalQuantity="selectedIntervalQuantity = $event"
                v-bind:splitByTimeline="selectedSplitByTimeline"
                @updateSplitByTimeline="selectedSplitByTimeline = $event"
              ></TsAggregationSelect>
            </v-card-text>
          </v-card>
        </v-stepper-content>

        <!-- <v-stepper-step step="2" editable>
          Configure upper/lower date bounds for events
        </v-stepper-step>
        <v-stepper-content step="2">
          <v-card>
            <v-card-text>
              <TsDateRangeSelect
                v-bind:range="selectedRange"
                @change="selectedRange = $event"
              ></TsDateRangeSelect>
            </v-card-text>
          </v-card>
        </v-stepper-content>

        <v-stepper-step step="3" editable>
          Apply existing/saved search parameters
        </v-stepper-step>
        <v-stepper-content step="3">
          <v-card>
            <v-card-text>
              <v-container>
                <v-row>
                  <v-col md="6">
                    <v-btn @click="loadSavedSearch">Load saved search</v-btn>
                  </v-col>
                  <v-col md="6">
                    <TsSavedSearchSelect
                      @updateSavedSearch="selectedSavedSearch = $event"
                    ></TsSavedSearchSelect>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col md="6">
                    <v-btn @click="loadRecentSearch">Load from recent search history</v-btn>
                  </v-col>
                  <v-col md="6">
                    <TsRecentSearchSelect
                      @updateRecentSearch="selectedRecentSearch = $event"
                    ></TsRecentSearchSelect>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col md="6">
                    <v-btn @click="loadCurrentSearch">Load current search</v-btn>
                  </v-col>
                </v-row>
              </v-container>
            </v-card-text>
          </v-card>
        </v-stepper-content>

        <v-stepper-step step="4" editable>
          Filter by timelines
        </v-stepper-step>
        <v-stepper-content step="4">
          <v-card>
            <v-card-text>
              <TsTimelineSelectTable
                v-bind:selectedTimelineIDs="selectedTimelineIDs"
                @change="selectedTimelineIDs = $event"
              ></TsTimelineSelectTable>
            </v-card-text>
          </v-card>
        </v-stepper-content>

        <v-stepper-step step="5" editable>
          Filter by query string
        </v-stepper-step>
        <v-stepper-content step="5">
          <v-card>
            <v-card-text>
              <v-text-field v-model="selectedQueryString" outlined clearable label="Enter query string"></v-text-field>
            </v-card-text>
          </v-card>
        </v-stepper-content>

        <v-stepper-step step="6" editable>
          Filter by term/label filters
        </v-stepper-step>
        <v-stepper-content step="6">
          <v-card>
            <v-card-text>
              <TsBooleanFilterList
                v-bind:selectedQueryChips="selectedQueryChips"
                @change="selectedQueryChips = $event"
              ></TsBooleanFilterList>
            </v-card-text>
          </v-card>
        </v-stepper-content> -->

        <v-stepper-step step="2" editable>
          Chart type
          <small>Select and configure chart visualization</small>
        </v-stepper-step>
        <v-stepper-content step="2">
          <v-card outlined>
            <v-card-text>
              <TsChartSelect
                v-bind:aggregatorType="selectedAggregator"
                v-bind:chartType="selectedChartType"
                @updateChartType="selectedChartType = $event"
                v-bind:title="selectedChartTitle"
                @updateTitle="selectedChartTitle = $event"
                v-bind:height="selectedHeight"
                @updateHeight="selectedHeight = $event"
                v-bind:width="selectedWidth"
                @updateWidth="selectedWidth = $event"
                v-bind:xTitle="selectedXTitle"
                @updateXTitle="selectedXTitle = $event"
                v-bind:showXLabels="selectedShowXLabels"
                @updateShowXLabels="selectedShowXLabels = $event"
                v-bind:yTitle="selectedYTitle"
                @updateYTitle="selectedYTitle = $event"
                v-bind:showYLabels="selectedYLabels"
                @updateYLabels="selectedYLabels = $event"
                v-bind:showDataLabels="selectedShowDataLabels"
                @updateShowDataLabels="selectedShowDataLabels = $event"
              >
              </TsChartSelect>
              <!-- <v-container>
                <v-row>
                  <v-col>
                    <v-text-field outlined label="Visualization title"></v-text-field>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col>
                    <v-text-field outlined label="Height"></v-text-field>
                  </v-col>
                  <v-col>
                    <v-text-field outlined label="Width"></v-text-field>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col>
                    <v-text-field outlined label="X-axis title"></v-text-field>
                  </v-col>
                  <v-col>
                    <v-checkbox label="Show x-axis labels"></v-checkbox>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col>
                    <v-text-field outlined label="Y-axis title"></v-text-field>
                  </v-col>
                  <v-col>
                    <v-checkbox label="Show y-axis labels"></v-checkbox>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col>
                    <v-checkbox label="Show data labels"></v-checkbox>
                  </v-col>
                </v-row>
              </v-container> -->
            </v-card-text>
          </v-card>
        </v-stepper-content>

        <v-stepper-step step="3" editable>
          Apply existing/recent/saved search parameters
          <small>Loading search parameters will overwrite any existing event filters</small>
        </v-stepper-step>
        <v-stepper-content step="3">
          <v-card>
            <v-card-text>
              <v-container>
                <v-row>
                  <v-col md="6">
                    <v-btn @click="loadSavedSearch">Load saved search</v-btn>
                  </v-col>
                  <v-col md="6">
                    <TsSavedSearchSelect
                      @updateSavedSearch="selectedSavedSearch = $event"
                    ></TsSavedSearchSelect>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col md="6">
                    <v-btn @click="loadRecentSearch">Load from recent search history</v-btn>
                  </v-col>
                  <v-col md="6">
                    <TsRecentSearchSelect
                      @updateRecentSearch="selectedRecentSearch = $event"
                    ></TsRecentSearchSelect>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col md="6">
                    <v-btn @click="loadCurrentSearch">Load current search</v-btn>
                  </v-col>
                  <v-col md="6">
                    <v-text-field
                      outlined
                      label="Current query string"
                      readonly
                      v-model="selectedQueryString"
                      ></v-text-field>
                  </v-col>
                </v-row>
              </v-container>
            </v-card-text>
          </v-card>
        </v-stepper-content>

        <v-stepper-step step="4" editable>
          Event filters
          <small>Select and configure filters to apply before aggregation</small>
        </v-stepper-step>
        <v-stepper-content step="4">
          <TsAggregationFiltersPanel
            v-bind:queryString="selectedQueryString"
            @updateFilterQueryString="selectedQueryString = $event"
            v-bind:timelineIDs="selectedTimelineIDs"
            @updateFilterTimelineIDs="selectedTimelineIDs = $event"
            v-bind:startDate="selectedRange.start"
            v-bind:endDate="selectedRange.end"
            @updateFilterDateRange="selectedRange = $event"
            v-bind:filterChips="selectedQueryChips"
            @updateFilterChips="selectedQueryChips = $event"
          ></TsAggregationFiltersPanel>
        </v-stepper-content>
      </v-stepper>
    </v-card-text>
    <v-card-actions>
      <v-btn color="primary" @click.stop="loadAggregationData">
        Load data
      </v-btn>
      <v-btn color="primary" @click.stop="showChartPreviewDialog = true">
        Preview chart
      </v-btn>
      <v-btn color="primary" @click="clear">
        Clear
      </v-btn>
      <!-- <v-btn color="primary" @click="cancel">
        Cancel
      </v-btn> -->
    </v-card-actions>
  </v-card>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsAggregationSelect from './AggregationSelect.vue'
// import TsTimelineSelectTable from './TimelineSelectTable.vue'
// import TsDateRangeSelect from './DateRangeSelect.vue'
// import TsBooleanFilterList from './BooleanFilterList.vue'
import TsSavedSearchSelect from './SavedSearchSelect.vue'
import TsRecentSearchSelect from './RecentSearchSelect.vue'
import TsChartSelect from './ChartSelect.vue'
import TsAggregationFiltersPanel from './AggregationFiltersPanel.vue'

export default {
  components: {
    //TsChartPreviewDialog,
    TsAggregationSelect,
    // TsDateRangeSelect,
    // TsTimelineSelectTable,
    // TsBooleanFilterList,
    TsRecentSearchSelect,
    TsSavedSearchSelect,
    TsChartSelect,
    TsAggregationFiltersPanel,
  },
  props: [
    'bucket', 'field', 'metric', 'interval',
    'intervalQuantity', 'aggregator', 'chartType',
    'range',
    'savedSearch', 'searchHistory', 'timelineIDs',
    'queryChips', 'queryString',
    'chartTitle', 'height', 'width', 'xTitle', 'yTitle',
    'showXLabels', 'showYLabels', 'showDataLabels'
  ],
  data() {
    return {
      currentStep: 1,
      selectedMaxItems: 10,
      selectedField: this.field,
      selectedMetric: this.metric,
      selectedInterval: { interval: 'y', max: 10 },
      selectedIntervalQuantity: this.intervalQuantity,
      selectedAggregator: this.aggregator,
      selectedSplitByTimeline: this.splitByTimeline,
      selectedChartType: this.chartType,
      selectedRange: this.range ? this.range : { start: '', end: '' },
      selectedSavedSearch: this.savedSearch,
      selectedSearchHistory: this.searchHistory,
      selectedTimelineIDs: this.timelineIDs,
      selectedQueryString: this.queryString,
      selectedQueryChips: this.queryChips,
      showChartPreviewDialog: false,
      selectedChartTitle: this.chartTitle,
      selectedHeight: this.height,
      selectedWidth: this.width,
      selectedXTitle: this.xTitle,
      selectedShowXLabels: this.showXLabels,
      selectedYTitle: this.yTitle,
      selectedYLabels: this.showYLabels,
      selectedShowDataLabels: this.showDataLabels,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    availableChartTypes() {
      return this.ch
    },
    currentQueryString() {
      const currentSearchNode = this.$store.state.currentSearchNode
      if (!currentSearchNode) {
        return ""
      }
      return currentSearchNode.query_string
    },
  },
  methods: {
    loadCurrentSearch() {
      const currentSearchNode = this.$store.state.currentSearchNode
      if (!currentSearchNode) {
        console.log('no current search...')
        return
      }

      const queryFilter = JSON.parse(currentSearchNode['query_filter'])
      this.selectedQueryString = currentSearchNode['query_string']
      this.selectedTimelineIDs = queryFilter.indices;
      this.selectedQueryChips = queryFilter.chips.filter(
        (chip) => chip.type === 'label' || chip.type === 'term' || chip.type === 'datetime_range'
      );

    },
    loadRecentSearch() {
      if (!this.selectedRecentSearch) {
        console.log('no search history')
        return
      }

      const queryFilter = JSON.parse(this.selectedRecentSearch['query_filter'])
      this.selectedQueryString = this.selectedRecentSearch['query_string']
      this.selectedTimelineIDs = queryFilter.indices;
      this.selectedQueryChips = queryFilter.chips.filter(
        (chip) => chip.type === 'label' || chip.type === 'term' || chip.type === 'datetime_range'
      );
    },
    loadSavedSearch() {
      if (!this.selectedSavedSearch) {
        console.log('no saved search')
        return
      }

      this.selectedQueryString = this.selectedSavedSearch.query;
      const queryFilter = JSON.parse(this.selectedSavedSearch.filter);
      this.selectedTimelineIDs = queryFilter.indices;
      this.selectedQueryChips = queryFilter.chips.filter(
        (chip) => chip.type === 'label' || chip.type === 'term' || chip.type === 'datetime_range'
      );
    },
    clear() {
      this.currentStep = 1
      this.selectedMaxItems = null
      this.selectedField = null
      this.selectedInterval = null
      this.selectedIntervalQuantity = null
      this.selectedMetric = null
      this.selectedAggregator = null
      this.selectedChartType = null
      this.selectedQueryString = null
      this.selectedRange = { start: '', end: '' }
      this.selectedTimelineIDs = []
      this.selectedQueryString = null
      this.selectedQueryChips = null
    },
    cancel() {
      this.clear()
      // :to="{ name: 'Explore' }"
    },
    aggregatorFormData() {
      return {
        name: '',
        description: '',
        agg_type: this.selectedAggregator,
        chart_type: this.selectedChartType,
        parameters: {

        }
      }
    },
    loadAggregationData() {
      let calendarInterval = `${this.selectedInterval.interval}${this.selectedIntervalQuantity}`

      let parameters = {
        aggregator_name: 'apex_chart',
        aggregator_parameters: {
          field: this.selectedField,
          aggregator_type: this.selectedAggregator,
          aggregator_options: {
            metric: this.selectedMetric,
            most_common_limit: this.selectedMaxItems,
            calendar_interval: calendarInterval,
          },
          chart_type: this.selectedChartType,
          filters: {
            query_string: this.selectedQueryString,
            start_datetime:  this.selectedRange.start,
            end_datetime:  this.selectedRange.end,
            query_chips: this.selectedQueryChips,
            timeline_ids: this.selectedTimelineIDs,
          },
        }
      }

      ApiClient.runAggregator(
        this.sketch.id, parameters
      ).then(
        (response) => {
          console.log(response)
        }
      ).catch(
        (e) => {
          console.error('Error running aggregator: ' + e)
        }
      )
    },
  },
  watch: {
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
