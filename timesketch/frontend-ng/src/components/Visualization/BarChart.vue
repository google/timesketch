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
      :series="series">
    </apexchart>
  </div>
</template>

<script>
import Apexchart from 'vue-apexcharts';
import EventBus from '../../main';

export default {
  props: {
    'chartSeries': { type: Object },
    'showDataLabels': { type: Boolean, default: false },
    'showTooltips': { type: Boolean, default: false },
    'showxaxisLabels': { type: Boolean, default: false },
    'showyaxisLabels': { type: Boolean, default: false },
    'xaxisTitle': { type: String, default: undefined },
    'xaxisType': { type: String, default: 'category' },
    'yaxisTitle': { type: String, default: undefined },
    'height': { type: Number, default: 250 },
    'width': { type: Number, default: 400 }
  },
  components: { Apexchart },
  data: function() {
    return {
      currentShowDataLabels: this.showDataLabels,
      currentShowToolTips: this.showTooltips,
      currentShowXAxisLabels: this.showxaxisLabels,
      currentShowYAxisLabels: this.showyaxisLabels,
      currentXAxisTitle: this.xaxis_title
    }
  },
  computed: {
    options() {
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
          // background: '#000',
          foreColor: '#fff',
          type: 'bar',
          zoom: {
            enabled: false,
            type: 'x',
            autoScaleYaxis: true,
          },
        },
        dataLabels: {
          enabled: this.showDataLabels,
        },
        noData: {
          text: 'Loading...'
        },
        plotOptions: {
          bar: {
            horizontal: true,
            dataLabels: {
              position: 'top',
            },
          },
        },
        tooltip: {
          enabled: this.showTooltips,
          followCursor: false,
          theme: 'dark',
        },
        xaxis: {
          type: this.xaxis_type,
          tickPlacement: 'on',
          labels: {
            show: this.showxaxisLabels,
          },
          title: {
            text: this.xaxis_title,
          },
        },
        yaxis: {
          type: this.yaxis_type,
          labels: {
            this: this.showyaxisLabels,
          },
          title: {
            text: this.yaxis_title,
          },
        }
      }
    },
    series() {
        let series = {
            name: 'Events',
            data: [],
        }
        return [series]
    }
  },
  methods: {
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
    }
  },
  created() {
    EventBus.$on('isDarkTheme', this.setTheme)
  },
  mounted() {
    this.setTheme()
  },
}

</script>
