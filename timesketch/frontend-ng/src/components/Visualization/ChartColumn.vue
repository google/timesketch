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
  <div>
    <apexchart
      :options="options"
      :series="series"
      :width="width"
      :height="height"
    >
    </apexchart>
  </div>
</template>

<script>
import Apexchart from 'vue-apexcharts';
import EventBus from '../../event-bus.js';

export default {
  props: {
    'fieldName': {
      type: String,
      default: 'Unknown field',
    },
    'metricName': {
      type: String,
      default: 'unknown metric',
    },
    'chartSeries': {
      type: Object,
      default: function() {
        return {}
      },
    },
    'chartLabels': {
      type: Array,
      default: function() {
        return []
      },
    },
    'chartType': {
      type: String,
      default: undefined,
    },
    'chartTitle': {
      type: String,
      default: undefined,
    },
    'height': {
      type: Number,
      default: 640,
    },
    'isTimeSeries': {
      type: Boolean,
      default: false,
    },
    'showDataLabels': {
      type: Boolean,
      default: true,
    },
    'showTooltips': {
      type: Boolean,
      default: true,
    },
    'showXLabels': {
      type: Boolean,
      default: true,
    },
    'showYLabels': {
      type: Boolean,
      default: true,
    },
    'width': {
      type: Number,
      default: 800,
    },
    'xTitle': {
      type: String,
      default: undefined,
    },
    'xType': {
      type: String,
      default: 'category',
    },
    'yTitle': {
      type: String,
      default: undefined,
    },
  },
  components: {
    Apexchart
  },
  data: function() {
    return {
    }
  },
  computed: {
    options: {
      get() {
        return {
          chart: {
            animations: {
              enabled: true,
              easing: 'easeinout',
              speed: 50,
              animateGradually: {
                enabled: true,
                delay: 50,
              },
              dynamicAnimation: {
                enabled: true,
                delay: 50,
              },
            },
            events: {
              dataPointSelection: (event, chartContext, config) => {
                this.filterDataPoint(config)
              }
            },
            type: 'bar',
            zoom: {
              enabled: false,
              type: 'x',
              autoScaleYaxis: true,
            },
            height: this.height,
            width: this.width,
          },
          labels: this.chartLabels,
          dataLabels: {
            enabled: this.showDataLabels,
          },
          noData: {
            text: 'Loading...'
          },
          plotOptions: {
            bar: {
              dataLabels: {
                position: 'top',
              },
            },
          },
          title: {
            text: this.chartTitle,
          },
          tooltip: {
            enabled: this.showTooltips,
            followCursor: false,
          },
          xaxis: {
            tickPlacement: 'on',
            labels: {
              show: this.showXLabels,
              hideOverlappingLabels: true,
            },
            title: {
              text: this.xTitle,
            },
            tooltip: {
              enabled: true,
            },
          },
          yaxis: {
            labels: {
              show: this.showYLabels,
            },
            title: {
              text: this.yTitle,
            },
          }
        }
      },
      set(newValue) {

      }
    },
    series() {
      if (this.fieldName === undefined || this.metricName === undefined) {
        return []
      }

      let series = {
          name: this.fieldName,
          data: this.chartSeries[this.metricName],
      }

      return [series]
    }
  },
  methods: {
    setTheme() {
      if (localStorage.isDarkTheme) {
        this.options = {
          chart: {
            foreColor: '#fff',
          },
          tooltip: {
            theme: 'dark',
          },
        }
      } else {
        this.options = {
          chart: {
            foreColor: '#333',
          },
          tooltip: {
            theme: 'light',
          },
        }
      }
    },
    filterDataPoint(config) {
      let eventData = {}
      eventData.doSearch = true

      let dataPointIndex = config.dataPointIndex
      if (this.isTimeSeries) {
        let start = this.chartLabels[dataPointIndex]
        let end = (dataPointIndex + 1 < this.chartLabels.length) ? this.chartLabels[dataPointIndex + 1] : ''

        if (end === "") {
          // exit early on last bucket
          return
        }
        eventData.doSearch = true
        eventData.queryString = this.fieldName + ':*'
        eventData.chip = {
          field: '',
          type: 'datetime_range',
          value: start + ',' + end,
          operator: 'must',
          active: true,
        }
        EventBus.$emit('setQueryAndFilter', eventData)
      } else {
        eventData.chip = {
          field: this.fieldName,
          value: config.w.config.labels[dataPointIndex],
          type: 'term',
          operator: 'must',
          active: true,
        }
        EventBus.$emit('setQueryAndFilter', eventData)
      }
    },
  },
  created() {
    EventBus.$on('isDarkTheme', this.setTheme)
  },
  mounted() {
    this.setTheme()
  },
}

</script>
