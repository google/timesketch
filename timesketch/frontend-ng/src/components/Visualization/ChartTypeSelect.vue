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
  <v-autocomplete
    outlined
    v-model="selectedChartType"
    :items="chartByAggregator"
    label="Chart type"
    @input="$emit('selectedChartType', $event)"
  >
    <template #item="{ item, on, attrs }">
      <v-list-item v-on="on" v-bind="attrs">
        <v-list-item-avatar>
        <v-icon> {{ item.icon }}</v-icon>
        </v-list-item-avatar>
        <v-list-item-content>
        {{ item.text }}
        </v-list-item-content>
      </v-list-item>
    </template>
    <template #selection="{ item }">
      <v-icon> {{ item.icon }} </v-icon>
      &nbsp; &nbsp; {{ item.text }}
    </template>
  </v-autocomplete>
</template>

<script>
export default {
  props: [
    'chart',
    'aggregator',
  ],
  data() {
    return {
      selectedChartType: this.chart,
      allChartTypes: [
        { text: 'bar', icon: 'mdi-poll mdi-rotate-90',},
        { text: 'column', icon: 'mdi-chart-bar', },
        { text: 'line', icon: 'mdi-chart-line', },
        { text: 'number', icon: 'mdi-numeric' },
        { text: 'table', icon: 'mdi-table'},
        { text: 'gantt', icon: 'mdi-chart-gantt'},
        { text: 'heatmap', icon: 'mdi-blur-linear'}
      ],
      seriesChartTypes: [
        { text: 'bar', icon: 'mdi-poll mdi-rotate-90',},
        { text: 'column', icon: 'mdi-chart-bar', },
        { text: 'line', icon: 'mdi-chart-line', },
        { text: 'table', icon: 'mdi-table'},
        { text: 'heatmap', icon: 'mdi-blur-linear'}
      ],
      singleMetricChartTypes: [
        { text: 'number', icon: 'mdi-numeric' },
      ]
    }
  },
  computed: {
    chartByAggregator() {
      console.log(this.aggregator)
      if (this.aggregator === 'rare_terms' ||
        this.aggregator === 'top_terms' ||
        this.aggregator === 'auto_date_histogram' ||
        this.aggregator === 'date_histogram') {
        return this.seriesChartTypes
      } else if (this.aggregator === 'single_metric') {
        return this.singleMetricChartTypes
      }
      return this.allChartTypes
    }
  },
  watch: {
    chart() {
        this.selectedChartType = this.chart
    }
  }
}
</script>
