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
  <div>
    <apexchart height="250" :options="options" :series="series"></apexchart>
  </div>
</template>

<script>
import Apexchart from 'vue-apexcharts'
import EventBus from '../../event-bus.js'

export default {
  props: ['chartData'],
  components: { Apexchart },
  data: function () {
    return {
      options: {
        chart: {
          type: 'bar',
          zoom: {
            enabled: false,
            type: 'x',
            autoScaleYaxis: true,
          },
          foreColor: '#fff',
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
              speed: 50,
            },
          },
          colors: ['#4285f'],
          toolbar: {
            show: true,
            tools: {
              download: false,
              selection: true,
              zoom: true,
              zoomin: true,
              zoomout: true,
            },
          },
          events: {
            dataPointSelection: (event, chartContext, config) => {
              this.emitFilterRequest(config)
            },
          },
        },
        tooltip: {
          enabled: true,
          followCursor: false,
          theme: 'dark',
          x: {
            formatter: (timestamp) => {
              const timerange = this.getBucketDateTimeRange(timestamp)
              const duration = this.$moment.duration(timerange.start.diff(timerange.end))
              return `${timerange.start.format('YYYY-MM-DD HH:mm:ss')} + ${duration.humanize()}`
            },
          },
        },
        plotOptions: {
          bar: {
            columnWidth: '95%',
            borderRadius: 4,
          },
        },
        dataLabels: {
          enabled: false,
        },
        grid: {
          xaxis: {
            lines: {
              show: false,
            },
          },
          yaxis: {
            lines: {
              show: false,
            },
          },
        },
        xaxis: {
          type: 'datetime',
          tickPlacement: 'on',
        },
      },
    }
  },
  computed: {
    series() {
      const series = {
        name: 'Events',
        data: [],
      }
      if (this.chartData) {
        series.data = Object.entries(this.chartData.data).map((e) => [parseInt(e[0]), e[1]])
        return [series]
      }
      return [series]
    },
  },
  methods: {
    getBucketDateTimeRange(timestamp) {
      const startDatetime = this.$moment.utc(timestamp)

      // Get bucket interval from Elasticsearch. Format: 3M, 1s etc
      const intervalSplit = this.chartData.interval.split(/(\d+)/)
      const intervalCount = intervalSplit[1]
      const intervalPeriod = intervalSplit[2]

      // Calculate the end of bucket time range using the interval
      const endDatetime = this.$moment.utc(timestamp).add(parseInt(intervalCount), intervalPeriod)
      return { start: startDatetime, end: endDatetime }
    },
    emitFilterRequest(config) {
      const dataPointIndex = config.selectedDataPoints[0][0]
      const series = config.w.config.series[0].data

      // Exit early if this is the last bucket.
      if (series.length === 1) {
        return
      }

      const timestamp = series[dataPointIndex][0]
      const timerange = this.getBucketDateTimeRange(timestamp)

      const chip = {
        field: '',
        type: 'datetime_range',
        value: timerange.start.toISOString() + ',' + timerange.end.toISOString(),
        operator: 'must',
        active: true,
      }
      this.$emit('addChip', chip)
    },
    setTheme() {
      if (localStorage.theme === 'dark') {
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
  },
  created() {
    // this.setTheme()
    EventBus.$on('isDarkTheme', this.setTheme)
  },
  mounted() {
    this.setTheme()
  },
}
</script>
