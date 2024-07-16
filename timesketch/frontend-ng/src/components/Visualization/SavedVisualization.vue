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
  <v-card class="mx-3" outlined>
    <ts-chart-card 
      v-if="aggregationId"
        :chartSeries="chartSeries" 
        :chartLabels="chartLabels"
        :chartTitle="chartTitle"
        :chartType="chartType"
        :fieldName="fieldName"
        :height="height"
        :isTimeSeries="isTimeSeries"
        :metricName="metricName"
        :showDataLabels="showDataLabels"
        :showXLabels="showXLabels"
        :showYLabels="showYLabels"
        :width="width"
        :xTitle="xTitle"
        :yTitle="yTitle"
      >
    </ts-chart-card>
  </v-card>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsChartCard from './ChartCard.vue'

export default {
  components: {
    TsChartCard,
  },
  props: [ 'aggregationId' ],
  data: function() {
    return {
      response: null,
      parameters: null,
      aggregationType: "",
      chartSeries: {},
      chartLabels: [],
      chartTitle: "",
      chartType: "",
      fieldName: "",
      height: 0,
      isTimeSeries: false,
      metricName: "",
      showDataLabels: false,
      showXLabels: false,
      showYLabels: false,
      width: 0,
      xTitle: "",
      yTitle: "",
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  methods: {
    loadAggregationData(savedAggregationId) {
      ApiClient.getAggregationById(
        this.sketch.id, this.aggregationId
      ).then(
        (response) => {
          const agg = response.data.objects[0]
          this.aggregationType = agg.agg_type
          this.parameters = JSON.parse(agg.parameters)
          
          ApiClient.runAggregator(
            this.sketch.id, this.parameters
          ).then(
            (response) => {
              const aggregationObj = response.data.objects[0][this.aggregationType]
              this.chartSeries = aggregationObj.buckets
              this.chartLabels = aggregationObj.labels
              this.chartTitle = aggregationObj.chart_options.chartTitle
              this.chartType = aggregationObj.chart_type
              this.fieldName = this.parameters.aggregator_parameters.fields[0].field
              this.height = aggregationObj.chart_options.height
              this.isTimeSeries = aggregationObj.chart_options.isTimeSeries
              this.metricName = this.parameters.aggregator_parameters.aggregator_options.metric
              this.showDataLabels = aggregationObj.chart_options.showDataLabels
              this.showXLabels = aggregationObj.chart_options.showXLabels
              this.showYLabels = aggregationObj.chart_options.showYLabels
              this.width = aggregationObj.chart_options.width
              this.xTitle = aggregationObj.chart_options.xTitle
              this.yTitle = aggregationObj.chart_options.yTitle
            }
          ).catch(
            (e) => {
              console.error('Error requesting aggregation data: ' + e)
            }
          )
        }
      ).catch(
        (e) => {
          console.error('Error requesting aggregation parameters: ' + e)
        }
      )
    }, 
  },
  watch: {
    aggregationId: function (newAggregationId) {
      if (newAggregationId) {
        this.loadAggregationData()
      }
    },
  },
  mounted() {
    if (this.aggregationId) {
      this.loadAggregationData()
    }
  },
}
</script>
