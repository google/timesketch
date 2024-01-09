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
  <v-container class="ma-0">
    <v-row>
      <v-col cols="12" md="12">
        <TsEventFieldSelect
          v-bind:field="selectedField"
          @selectedField="selectedField = $event"
        >
        </TsEventFieldSelect>
      </v-col>
    </v-row>
    <!-- <v-row>
      <v-col>
        <TsChartSelect
          v-bind:chart="selectedChartType"
          @selectedChartType="selectedChartType = $event"
        >
        </TsChartSelect>
      </v-col>
    </v-row> -->
    <v-row>
      <v-col>
        <v-autocomplete
          outlined
          v-model="selectedAggregator"
          :disabled="selectedField == null"
          :items="getAggregator"
          label="Aggregate events by"
        ></v-autocomplete>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" md="6">
        <v-autocomplete
          outlined
          v-model="selectedMetric"
          :disabled="!(selectedAggregator &&
            (selectedAggregator === 'date_histogram' ||
             selectedAggregator === 'single_metric')
          )"
          :items="metrics"
          label="Metric"
        ></v-autocomplete>
      </v-col>
      <v-col cols="12" md="6">
        <v-select
          outlined
          v-model="selectedMaxItems"
          :disabled="!(selectedAggregator &&
            (selectedAggregator === 'top_terms' ||
             selectedAggregator === 'significant_terms' ||
             selectedAggregator === 'auto_date_histogram')
          )"
          :items="[...Array(50).keys()].map((_, i) => i + 1)"
          label="Maximum number of items (K)"
        ></v-select>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" md="6">
        <v-autocomplete
          outlined
          :disabled="!(selectedAggregator && selectedAggregator === 'date_histogram')"
          v-model="selectedInterval"
          :items="allCalendarIntervals"
          label="Calendar interval"
        ></v-autocomplete>
      </v-col>
      <v-col cols="12" md="6">
        <v-select
          outlined
          v-model="selectedIntervalQuantity"
          :disabled="!(selectedAggregator && selectedAggregator === 'date_histogram')"
          :items="intervalQuantities"
          label="Calendar Interval quantity"
        ></v-select>
      </v-col>
      <!-- <v-col cols="12" md="6">
        <v-checkbox
          v-model="splitByTimeline"
          label="Split by timeline"
        ></v-checkbox>
      </v-col> -->
    </v-row>
  </v-container>
</template>

<script>
import TsEventFieldSelect from './EventFieldSelect.vue'
// import TsChartSelect from './ChartSelect.vue'

export default {
  components: {
    TsEventFieldSelect,
    // TsChartSelect
  },
  props: [
    'field',
    // 'chart',
    'aggregator',
    'metric',
    'maxItems',
    'interval',
    'intervalQuantity',
    'splitByTimeline',
  ],
  data() {
    return {
      selectedField: this.field,
      // selectedChartType: this.chart,
      selectedAggregator: this.aggregator,
      selectedMetric: this.metric,
      selectedMaxItems: this.maxItems,
      selectedInterval: this.interval,
      selectedIntervalQuantity: this.intervalQuantity,
      selectedSplitByTimeline: this.splitByTimeline,
      enableCalendarInterval: false,
      intMetrics: [
        { text: 'Average', value: 'avg' },
        { text: 'Count', value: 'count' },
        { text: 'Minimum', value: 'min' },
        { text: 'Maximum', value: 'max' },
        { text: 'Sum', value: 'sum' },
        { text: 'Unique', value: 'cardinality' },
      ],
      stringAggregators: [
        { text: 'Time interval', value: 'date_histogram' },
        { text: 'Top K terms', value: 'top_terms' },
      ],
      allAggregators: [
        { text: 'Rare terms', value: 'rare_terms' },
        // { text: 'Significant terms', value: 'significant_terms' }, // podium-gold
        { text: 'Single', value: 'single_metric' },
        { text: 'Auto Time Interval', value: 'auto_date_histogram' },
        { text: 'Time interval', value: 'date_histogram' },
        { text: 'Top K terms', value: 'top_terms' },
      ],
      stringMetrics: [
        { text: 'Count', value: 'count' },
        // { text: 'Unique', value: 'cardinality' },
      ],
      allCalendarIntervals: [
        { text: 'Year', value: { interval: 'y', max: 10 } },
        { text: 'Quarter', value: { interval: 'q', max: 4 } },
        { text: 'Month', value: { interval: 'M', max: 12 } },
        { text: 'Week', value: { interval: 'w', max: 52 } },
        { text: 'Day', value: { interval: 'd', max: 31 } },
        { text: 'Hour', value: { interval: 'h', max: 24 } },
        { text: 'Minute', value: { interval: 'm', max: 60 } },
      ],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    metrics() {
      if (this.selectedField == null)
        return []

      if (this.selectedField.type === 'text') {
        return this.stringMetrics
      }
      else {
        return this.intMetrics
      }
    },
    intervalQuantities() {
      if (this.selectedInterval == null) {
        return []
      }
      return [...Array(this.selectedInterval.max - 1).keys()].map((_, i) => i + 1)
    },
    getAggregator() {
      if (this.selectedField == null) {
        return []
      }

      if (this.selectedField.type === 'text') {
        return this.stringAggregators
      }

      return this.allAggregators
      // const chartType = this.selectedChartType
      // const chartAggregators = {
      //   'bar': this.stringAggregators,
      //   'column': this.stringAggregators,
      //   'line': this.stringAggregators,
      //   'number': [{ text: 'Single metric', value: 'single_metric' }],
      //   'table': this.allAggregators,
      //   'gantt': [{ text: 'Time interval', value: 'date_histogram' }],
      //   'heatmap': [{ text: 'Time interval', value: 'date_histogram' }],
      // }

      // if (chartType == null || !(chartType in chartAggregators) ) {
      //   return []
      // }

      // return chartAggregators[chartType]
    },
  },
  watch: {
    field() {
      this.selectedField = this.field
    },
    // chart() {
    //   this.selectedChartType = this.chart
    // },
    aggregator() {
      this.selectedAggregator = this.aggregator
    },
    metric() {
      this.selectedMetric = this.metric
    },
    maxItems() {
      this.selectedMaxItems = this.maxItems
    },
    interval() {
      this.selectedInterval = this.interval
    },
    intervalQuantity() {
      this.selectedIntervalQuantity = this.intervalQuantity
    },
    selectedField() {
      this.$emit('updateField', this.selectedField)
    },
    // selectedChartType() {
    //   this.$emit('updateChart', this.selectedChartType)
    // },
    selectedAggregator() {
      this.$emit('updateAggregator', this.selectedAggregator)
    },
    selectedMetric() {
      this.$emit('updateMetric', this.selectedMetric)
    },
    selectedMaxItems() {
      this.$emit('updateMaxItems', this.selectedMaxItems)
    },
    selectedInterval() {
      this.$emit('updateInterval', this.selectedInterval)
    },
    selectedIntervalQuantity() {
      this.$emit('updateIntervalQuantity', this.selectedIntervalQuantity)
    },
    selectedSplitByTimeline() {
      this.$emit('updateSplitByTimeline', this.splitByTimeline)
    },
  }
}
</script>
