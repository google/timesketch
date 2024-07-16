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
  <v-btn-toggle v-model="chartSelector" mandatory>
    <v-btn
    v-for="(item, index) in chartByAggregator"
    :key="index"
    @click="$emit('selectedChartType', item.text)"
    :title="item.text"
    :disabled="chartSelectorDisabled"
    >
      <v-icon>{{ item.icon }}</v-icon>
    </v-btn>
  </v-btn-toggle>
</template>

<script>
export default {
  props: {
    aggregator: {
      type: String,
    },
    chart: {
      type: String,
    }
  },
  data() {
    return {
      chartSelector: 0,
      selectedChartType: this.chart,
      chartTypes: [
        {
          text: 'bar',
          icon: 'mdi-poll mdi-rotate-90',
        },
        {
          text: 'column',
          icon: 'mdi-chart-bar',
        },
        {
          text: 'line',
          icon: 'mdi-chart-line',
        },
        {
          text: 'table',
          icon: 'mdi-table',
        },
        // {
        //   text: 'gantt',
        //   icon: 'mdi-chart-gantt',
        // },
        {
          text: 'heatmap',
          icon: 'mdi-blur-linear',
        },
        {
          text: 'donut',
          icon: 'mdi-chart-donut',
        }
      ],
      seriesChartTypes: [
        {
          text: 'bar',
          icon: 'mdi-poll mdi-rotate-90',
        },
        {
          text: 'column',
          icon: 'mdi-chart-bar',
        },
        {
          text: 'line',
          icon: 'mdi-chart-line',
        },
        {
          text: 'table',
          icon: 'mdi-table',
        },
        {
          text: 'heatmap',
          icon: 'mdi-blur-linear',
        },
      ],
      singleMetricChartTypes: [
        // {
        //   text: 'number',
        //   icon: 'mdi-numeric'
        // },
        // {
        //   text: 'table',
        //   icon: 'mdi-table',
        // },
      ]
    }
  },
  computed: {
    allChartTypes() {
      const uniqueChartText = new Set();
      const uniqueChartTypes = [];

      for (const chartType of [...this.chartTypes, ...this.seriesChartTypes, ...this.singleMetricChartTypes]) {
        if (!uniqueChartText.has(chartType.text)) {
          uniqueChartText.add(chartType.text);
          uniqueChartTypes.push(chartType);
        }
      }
      return uniqueChartTypes;
    },
    chartByAggregator() {
      if (this.aggregator === 'top_terms') {
        return this.chartTypes
      } else if (
        this.aggregator === 'rare_terms' ||
        this.aggregator === 'auto_date_histogram' ||
        this.aggregator === 'calendar_date_histogram'
      ) {
        return this.seriesChartTypes
      }
      else if (this.aggregator === 'single_metric') {
        return this.singleMetricChartTypes
      }
      return this.allChartTypes
    },
    chartSelectorDisabled() {
      return !this.aggregator
    }
  },
  watch: {
    aggregator() {
      if (this.chartByAggregator) {
        this.selectedChartType = this.chartByAggregator[0].text
        this.$emit('selectedChartType', this.selectedChartType)
      }
    },
    chart() {
      this.selectedChartType = this.chart
    }
  }
}
</script>
