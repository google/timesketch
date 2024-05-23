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
  <v-card flat>
    <v-card-title>
      Create new visualization using aggregated events
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="4">
          <v-card outlined>
            <v-card-text>
              <TsAggregationConfig
                :field="selectedField"
                @updateField="selectedField = $event"
                :aggregator="selectedAggregator"
                @updateAggregator="selectedAggregator = $event"
                :metric="selectedMetric"
                @updateMetric="selectedMetric = $event"
                :maxItems="selectedMaxItems"
                @updateMaxItems="selectedMaxItems = $event"
                :interval="selectedInterval"
                @updateInterval="selectedInterval = $event"
                :intervalQuantity="selectedIntervalQuantity"
                @updateIntervalQuantity="selectedIntervalQuantity = $event"
                :splitByTimeline="selectedSplitByTimeline"
                @updateSplitByTimeline="selectedSplitByTimeline = $event"
              ></TsAggregationConfig>
              <TsChartConfig
                :aggregatorType="selectedAggregator"
                :chartType="selectedChartType"
                @updateChartType="selectedChartType = $event"
                :title="selectedChartTitle"
                @updateTitle="selectedChartTitle = $event"
                :height="selectedHeight"
                @updateHeight="selectedHeight = $event"
                :width="selectedWidth"
                @updateWidth="selectedWidth = $event"
                :xTitle="selectedXTitle"
                @updateXTitle="selectedXTitle = $event"
                :showXLabels="selectedShowXLabels"
                @updateShowXLabels="selectedShowXLabels = $event"
                :yTitle="selectedYTitle"
                @updateYTitle="selectedYTitle = $event"
                :showYLabels="selectedShowYLabels"
                @updateShowYLabels="selectedShowYLabels = $event"
                :showDataLabels="selectedShowDataLabels"
                @updateShowDataLabels="selectedShowDataLabels = $event"
              ></TsChartConfig>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="8">
          <v-card outlined>
            <v-card-text>
              <TsChartCard
                v-if="chartSeries && selectedChartType"
                :fieldName="selectedField.field"
                :metricName="selectedMetric"
                :is-time-series="selectedAggregator ? selectedAggregator.endsWith('date_histogram') : false"
                :chartSeries="chartSeries" 
                :chartLabels="chartLabels"
                :chartTitle="selectedChartTitle"
                :chartType="selectedChartType"
                :height="selectedHeight"
                :width="selectedWidth"
                :xTitle="selectedXTitle"
                :showXLabels="selectedShowXLabels"
                :yTitle="selectedYTitle"
                :showYLabels="selectedShowYLabels"
                :showDataLabels="selectedShowDataLabels"
              ></TsChartCard>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-card-text>
    <v-card-actions>
      <v-btn color="primary" 
        @click="loadAggregationData"
        :disabled="!(
          selectedField && 
          selectedAggregator && 
          selectedChartType
        )"
      >
        Load/refresh data
      </v-btn>
      <v-btn 
        color="primary"
        :disabled="response == null || !selectedChartTitle"
        @click="saveVisualization"
      >
        Save
      </v-btn>
      <v-btn 
        color="primary" 
        @click="clear"
      >
        Clear
      </v-btn>
      <v-btn 
        color="primary" 
        @click="clear" 
        :to="{ name: 'Explore' }"
      >
        Cancel
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsAggregationConfig from './AggregationConfig.vue'
import TsChartConfig from './ChartConfig.vue'
import TsChartCard from './ChartCard.vue'

export default {
  components: {
    TsAggregationConfig,
    TsChartConfig,
    TsChartCard,
  },
  props: {
    aggregator: {
      type: String,
    },
    bucket: {
      type: Number,
    },
    chartTitle: {
      type: String,
    },
    chartType: {
      type: String,
      default: 'bar',
    },
    field: {
      type: String,
    },
    height: {
      type: Number,
      default: 600,
    },
    interval: {
      type: Object,
      default: function() {
        return { 
          interval: 'year', 
          max: 10 
        }
      },
    },
    intervalQuantity: {
      type: Number,
    },
    metric: {
      type: String,
    },
    queryChips: {
      type: Array,
    },
    queryString: {
      type: String,
    },
    range: {
      type: Object,
      default: function() {
        return { 
          start: '', end: '' 
        }
      }
    },
    savedSearch: {
      type: Boolean,
      default: true,
    },
    searchHistory: {
      type: Boolean,
      default: true,
    },
    showDataLabels: {
      type: Boolean,
      default: true,
    },
    showXLabels: {
      type: Boolean,
      default: true,
    },
    showYLabels: {
      type: Boolean,
      default: true,
    },
    timelineIDs: {
      type: Array,
      default: function() {
        return []
      },
    },
    width: {
      type: Number,
      default: 800,
    },
    xTitle: {
      type: String,
    },
    yTitle: {
      type: String,
    },
  },
  data() {
    return {
      currentStep: 1,
      responseMeta: null,
      response: null,
      selectedAggregator: this.aggregator,
      selectedChartTitle: this.chartTitle,
      selectedChartType: this.chartType,
      selectedMaxItems: 10,
      selectedField: this.field,
      selectedHeight: this.height,
      selectedInterval: this.interval,
      selectedIntervalQuantity: this.intervalQuantity,
      selectedMetric: this.metric,
      selectedQueryString: this.queryString,
      selectedQueryChips: this.queryChips,
      selectedRange: this.range,
      selectedSavedSearch: this.savedSearch,
      selectedSearchHistory: this.searchHistory,
      selectedShowDataLabels: this.showDataLabels,
      selectedShowXLabels: this.showXLabels,
      selectedShowYLabels: this.showYLabels,
      selectedSplitByTimeline: this.splitByTimeline,
      selectedTimelineIDs: this.timelineIDs,
      selectedWidth: this.width,
      selectedXTitle: this.xTitle,
      selectedYTitle: this.yTitle,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    chartSeries() {
      if (this.response !== null && this.response.buckets !== null) {
        return this.response.buckets
      }
      return undefined
    },
    chartLabels() {
      if (this.response !== null && this.response.labels !== null) {
        return this.response.labels
      }
      return undefined
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
      this.responseMeta = null
      this.response = null
      this.selectedAggregator = this.aggregator
      this.selectedChartTitle = this.chartTitle
      this.selectedChartType = this.chartType
      this.selectedMaxItems = 10
      this.selectedField = this.field
      this.selectedHeight = this.height
      this.selectedInterval = this.interval
      this.selectedIntervalQuantity = this.intervalQuantity
      this.selectedMetric = this.metric
      this.selectedQueryString = this.queryString
      this.selectedQueryChips = this.queryChips
      this.selectedRange = this.range
      this.selectedSavedSearch = this.savedSearch
      this.selectedSearchHistory = this.searchHistory
      this.selectedShowDataLabels = this.showDataLabels
      this.selectedShowXLabels = this.showXLabels
      this.selectedShowYLabels = this.showYLabels
      this.selectedSplitByTimeline = this.splitByTimeline
      this.selectedTimelineIDs = this.timelineIDs
      this.selectedWidth = this.width
      this.selectedXTitle = this.xTitle
      this.selectedYTitle = this.yTitle
    },
    saveVisualization() {
      if (this.response != null) {
        
        ApiClient.saveAggregation(
          this.sketch.id,
          this.responseMeta,
          this.selectedChartTitle,
          this.getAggregatorParameters(),
        ).then(() => {
          this.$store.dispatch('updateSavedVisualizationList', this.sketch.id)
          this.successSnackBar('Visualization added: ' + this.selectedChartTitle)
        }).catch((e) => {
          this.errorSnackBar('Error adding visualization: ' + this.selectedChartTitle)
        })
      }
    },
    getAggregatorParameters() {
      return {
        aggregator_name: this.selectedAggregator,
        aggregator_class: 'apex',
        aggregator_parameters: {
          fields: [this.selectedField],
          aggregator_options: {
            query_string: this.selectedQueryString,
            start_time:  this.selectedRange.start,
            end_time:  this.selectedRange.end,
            query_chips: this.selectedQueryChips,
            timeline_ids: this.selectedTimelineIDs,
            metric: this.selectedMetric,
            max_items: this.selectedMaxItems,
            calendar_interval: this.selectedInterval.interval,
          },
          chart_type: this.selectedChartType,
          chart_options: {
            chartTitle: this.selectedChartTitle,
            height: this.selectedHeight,
            isTimeSeries: this.selectedAggregator.endsWith('date_histogram'),
            showDataLabels: this.selectedShowDataLabels,
            showXLabels: this.selectedShowXLabels,
            showYLabels: this.selectedShowYLabels,
            width: this.selectedWidth,
            xTitle: this.selectedXTitle,
            yTitle: this.selectedYTitle,
          },
        }
      }
    },
    loadAggregationData() {
      let parameters = this.getAggregatorParameters()

      ApiClient.runAggregator(
        this.sketch.id, parameters
      ).then(
        (response) => {
          this.responseMeta = response.data.meta
          this.response = response.data.objects[0][this.selectedAggregator]
        }
      ).catch(
        (e) => {
          console.error('Error running aggregator: ' + e)
        }
      )
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
</style>
