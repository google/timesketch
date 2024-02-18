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
  <v-card flat>
    <v-card-title 
      v-if="chartTitle !== undefined"
    >
      {{ chartTitle }}
    </v-card-title>
    <v-card-text>
      <v-data-table
        :headers="headers"
        :items="items"
        dense
      >
        <template v-slot:header.field="{ header }">
          {{ header.text }} 
        </template>
        <template v-slot:item.field="{ item }">
          <v-container
            class="pl-0"
            @mouseover="c_key = item.field"
            @mouseleave="c_key = -1"
          >
            {{ item.field }}
            <v-btn 
              @click.stop="applyFilterChip(fieldName, item.field, 'must')" 
              v-if="item.field == c_key && !isTimeSeries" 
              icon 
              x-small 
              class="mr-1"
            >
              <v-icon :title="'Filter for value ' + item.field">
                mdi-filter-plus-outline
              </v-icon>
            </v-btn>
            <v-btn
              @click.stop="applyFilterChip(fieldName, item.field, 'must_not')"
              v-if="item.field == c_key && !isTimeSeries" 
              icon
              x-small
              class="mr-1"
            >
              <v-icon :title="'Filter out value ' + item.field">
                mdi-filter-minus-outline
              </v-icon>
            </v-btn>
            <v-btn
              v-if="item.field == c_key" 
              icon
              x-small
              style="cursor: pointer"
              @click="copyToClipboard(item.field)"
              class="pr-1"
            >
              <v-icon 
                :title="'Copy value ' + item.field" 
                small
              >
                mdi-content-copy
              </v-icon>
            </v-btn>
          </v-container>
        </template>
        <template v-slot:item.metric="{ item }">
          <v-container
            class="pl-0"
            @mouseover="c_key = item.field"
            @mouseleave="c_key = -1"
          >
            {{ item.metric }}
            <v-btn
              v-if="item.field == c_key"
              icon
              x-small
              style="cursor: pointer"
              @click="copyToClipboard(item.metric)"
              class="pr-1"
            >
              <v-icon 
              :title="'Copy value ' + item.metric" 
                small
              >
                mdi-content-copy
              </v-icon>
            </v-btn>
          </v-container>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script>
import EventBus from '../../event-bus.js'

export default {
  props: {
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
    'chartTitle': {
      type: String,
      default: undefined
    },
    'fieldName': {
      type: String,
      default: 'Unknown field',
    },
    'height': { 
      type: Number, 
      default: 640, 
    },
    'isTimeSeries': {
      type: Boolean,
      default: false,
    },
    'metricName': {
      type: String,
      default: 'unknown metric',
    },
    'width': { 
      type: Number, 
      default: 800, 
    },
  },
  data: function() {
    return {
      c_key: -1,
    }        
  },
  computed: {
    items() {
      let tableItems = []
      if (this.metricName in this.chartSeries) {
        for (let i = 0, len = this.chartLabels.length; i < len; i++) {
          let o = {
            field: this.chartLabels[i], 
            metric: this.chartSeries[this.metricName][i],
          }
          tableItems.push(o)
        }
      }
      return tableItems
    },
    headers() {
      return [
        { 
          text: this.fieldName, 
          value: 'field', 
          width: "80%" 
        },
        { 
          text: this.metricName, 
          value: 'metric'
        },
      ]
    },
  },
  methods: {
    copyToClipboard(content) {
      try {
        navigator.clipboard.writeText(content)
        this.infoSnackBar('Copied ' + content + ' to the clipboard')
      } catch (error) {
        this.errorSnackBar('Failed copying to the clipboard!')
        console.error(error)
      }
    },
    applyFilterChip(key, value, operator) {
      if (this.isTimeSeries) {
        return
      }
      let eventData = {}
      eventData.doSearch = true
      let chip = {
        field: key,
        value: value,
        type: 'term',
        operator: operator,
        active: true,
      }
      eventData.chip = chip
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
}
</script>
