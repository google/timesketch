<!--
 Copyright 2024 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 -->
 <template>
  <v-card
    flat
    :min-height="height"
    :min-width="width"
  >
    <v-card-text>
      <TsBarChart
        v-if="chartSeries != null && chartType === 'bar'"
        :fieldName="fieldName"
        :metricName="metricName"
        :is-time-series="isTimeSeries"
        :chartSeries="chartSeries"
        :chartLabels="chartLabels"
        :chartTitle="chartTitle"
        :height="height"
        :width="width"
        :xTitle="xTitle"
        :showXLabels="showXLabels"
        :yTitle="yTitle"
        :showYLabels="showYLabels"
        :showDataLabels="showDataLabels"
      >
      </TsBarChart>
      <TsColumnChart
        v-if="chartSeries != null && chartType === 'column'"
        :fieldName="fieldName"
        :metricName="metricName"
        :is-time-series="isTimeSeries"
        :chartSeries="chartSeries"
        :chartLabels="chartLabels"
        :chartTitle="chartTitle"
        :height="height"
        :width="width"
        :xTitle="xTitle"
        :showXLabels="showXLabels"
        :yTitle="yTitle"
        :showYLabels="showYLabels"
        :showDataLabels="showDataLabels"
      >
      </TsColumnChart>
      <TsDonutChart
        v-if="chartSeries != null && chartType === 'donut'"
        :fieldName="fieldName"
        :metricName="metricName"
        :is-time-series="isTimeSeries"
        :chartSeries="chartSeries"
        :chartLabels="chartLabels"
        :chartTitle="chartTitle"
        :height="height"
        :width="width"
        :xTitle="xTitle"
        :showXLabels="showXLabels"
        :yTitle="yTitle"
        :showYLabels="showYLabels"
        :showDataLabels="showDataLabels"
      >
      </TsDonutChart>
      <TsHeatmapChart
        v-if="chartSeries != null && chartType === 'heatmap'"
        :fieldName="fieldName"
        :metricName="metricName"
        :is-time-series="isTimeSeries"
        :chartSeries="chartSeries"
        :chartLabels="chartLabels"
        :chartTitle="chartTitle"
        :height="height"
        :width="width"
        :xTitle="xTitle"
        :showXLabels="showXLabels"
        :yTitle="yTitle"
        :showYLabels="showYLabels"
        :showDataLabels="showDataLabels"
      >
      </TsHeatmapChart>
      <TsLineChart
        v-if="chartSeries != null && chartType === 'line'"
        :fieldName="fieldName"
        :metricName="metricName"
        :is-time-series="isTimeSeries"
        :chartSeries="chartSeries"
        :chartLabels="chartLabels"
        :chartTitle="chartTitle"
        :height="height"
        :width="width"
        :xTitle="xTitle"
        :showXLabels="showXLabels"
        :yTitle="yTitle"
        :showYLabels="showYLabels"
        :showDataLabels="showDataLabels"
      >
      </TsLineChart>
      <TsTableChart
        v-if="chartSeries != null && chartType === 'table'"
        :fieldName="fieldName"
        :metricName="metricName"
        :is-time-series="isTimeSeries"
        :chartSeries="chartSeries"
        :chartLabels="chartLabels"
        :chartTitle="chartTitle"
        :height="height"
        :width="width"
      >
      </TsTableChart>
    </v-card-text>
  </v-card>
 </template>

 <script>
import TsBarChart from './ChartBar.vue'
import TsColumnChart from './ChartColumn.vue'
import TsDonutChart from './ChartDonut.vue'
import TsHeatmapChart from './ChartHeatmap.vue'
import TsLineChart from './ChartLine.vue'
import TsTableChart from './ChartTable.vue'

 export default {
  components: {
    TsBarChart,
    TsColumnChart,
    TsDonutChart,
    TsHeatmapChart,
    TsLineChart,
    TsTableChart,
  },
  props: {
    chartLabels: {
      type: Array,
    },
    chartSeries: {
      type: Object,
    },
    chartTitle: {
      type: String,
      default: undefined,
    },
    chartType: {
      type: String,
    },
    fieldName: {
      type: String,
    },
    height: {
      type: Number,
    },
    isTimeSeries: {
      type: Boolean,
    },
    metricName: {
      type: String,
    },
    showDataLabels: {
      type: Boolean,
    },
    showXLabels: {
      type: Boolean,
    },
    showYLabels: {
      type: Boolean,
    },
    width: {
      type: Number,
    },
    xTitle: {
      type: String,
    },
    yTitle: {
      type: String,
    },
  }
 }
</script>
