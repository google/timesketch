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
  <div :style="{width: '100%', height: '100%'}">
    <div>
      {{ chartTitle }}
    
    </div>
    <div :style="{'text-align': 'center', 'font-size': '5vmax', 'vertical-align': 'text-bottom'}">
      {{  chartSeries[fieldName][0] }}
    </div>
  </div>
</template>

<script>
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
    'width': { 
      type: Number, 
      default: 800, 
    },
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
  },
  created() {
    EventBus.$on('isDarkTheme', this.setTheme)
  },
  mounted() {
    this.setTheme()
  },
}

</script>
