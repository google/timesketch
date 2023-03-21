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
  <v-card class="mx-auto">
    <v-card-title>
      <span class="headline">Event Data Analytics</span>
      <v-spacer></v-spacer>
      <v-btn icon>
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-subtitle>
      <span class="text-h6">Field:&nbsp;<span style="font-family: monospace">{{ eventKey }}</span> | Value: &nbsp;<span style="font-family: monospace">{{ eventValue }}</span></span>
    </v-card-subtitle>
    <v-card-text>
      <v-container fluid>
        <v-row justify="center">
          <v-col>
            <v-card height="450px" :loading="!statsReady">
              <v-card-title>
                General statistics
              </v-card-title>
              <v-card-text>
                <ul>
                  <li>Total number of events: {{ this.docCount }}</li>
                  <ul>
                    <li>Min date: {{ this.fieldDateTimeMinimum }}</li>
                    <li>Max date: {{ this.fieldDateTimeMaximum }}</li>
                  </ul>
                </ul>
                <br>
                <ul>
                  <li>Selected Field:&nbsp;<span style="font-family: monospace">{{  this.eventKey }}</span></li>
                  <ul>
                    <li>Count: {{ this.fieldValueCount }}</li>
                    <li>Unique: {{ this.fieldCardinality }}</li>
                  </ul>
                </ul>
                <br>
                <ul>
                  <li>Selected Value:&nbsp;<span style="font-family: monospace">{{  this.eventValue }}</span></li>
                  <ul>
                    <li>Count: {{ this.valueEventCount }}</li>
                    <li>Min date: {{ this.valueDateTimeMinimum }}</li>
                    <li>Max date: {{ this.valueDateTimeMaximum }}</li>
                  </ul>
                </ul>

              </v-card-text>
            </v-card>
          </v-col>
          <v-col align="center">
            <v-card height="450px" :loading="!statsReady">
              <v-card-title>
                Count of &nbsp;<span style="font-family: monospace">{{ eventValue }}</span>&nbsp; as a percentage of &nbsp;<span style="font-family: monospace">{{ eventKey }}</span>&nbsp; events
              </v-card-title>
              <v-card-text v-if="statsReady">
                <apexchart
                  height="250px"
                  :options="this.donutChartOptions"
                  :series="this.donutChartSeries"
                ></apexchart>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col align="center">
            <v-card height="450px" :loading="!statsReady">
              <v-card-title>
                Event distribution by {{ this.distributionIntervals[this.selectedDistributionIntervalIndex] }}
              </v-card-title>
              <v-card-subtitle>
                Selected value:&nbsp;<span style="font-family: monospace">{{ eventValue }}</span>&nbsp;
              </v-card-subtitle>
              <v-card-text v-if="statsReady">
                <v-btn-toggle mandatory v-model="selectedDistributionIntervalIndex">
                  <v-btn v-for="interval in this.distributionIntervals" :key="interval" small>
                    {{ interval }}
                  </v-btn>
                </v-btn-toggle>
                <apexchart
                  height="300px"
                  :options="this.intervalChartOptions"
                  :series="this.intervalChartSeries"
                ></apexchart>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        <v-row>
            <v-col align="center">
              <v-card height="500px" :loading="!statsReady">
                <v-card-title>
                  Top {{ Math.min(10, this.commonValues.length) }} &nbsp;<span style="font-family: monospace">{{ eventKey }}</span>&nbsp; values (out of {{ this.fieldCardinality }})
                </v-card-title>
                <v-card-text>
                  <v-data-table
                    :headers="termHeaders"
                    :items="commonValues"
                    :items-per-page="10"
                    dense
                  >
                  </v-data-table>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col align="center">
              <v-card height="500px" :loading="!statsReady">
                <v-card-title>
                  Rare &nbsp;<span style="font-family: monospace">{{ eventKey }}</span>&nbsp; values (max count of 5)
                </v-card-title>
                <v-card-text>
                  <v-data-table
                    :headers="termHeaders"
                    :items="rareValues"
                    :items-per-page="10"
                    dense
                  >
                  </v-data-table>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col align="center">
            <v-card height="500px" :loading="!statsReady">
              <v-card-title>
                Event distribution by hour/day of week
              </v-card-title>
              <v-card-subtitle>
                Selected value:&nbsp;<span style="font-family: monospace">{{ eventValue }}</span>&nbsp;
              </v-card-subtitle>
              <v-card-text v-if="statsReady">
                <apexchart
                  height="400px"
                  :options="this.intervalHeatmapOptions"
                  :series="this.intervalHeatmapSeries"
                ></apexchart>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-card-text>
  </v-card>
</template>

<script>
import Apexchart from 'vue-apexcharts'
import ApiClient from '../../utils/RestApiClient'

export default {
  components: {
    Apexchart
  },
  props: [
    'eventKey',
    'eventValue',
    'eventTimestamp',
    'eventTimestampDesc',
    'sketchId'
  ],
  data() {
    return {
      distributionIntervals: [
        "Year",
        "Month",
        "Day",
        "Hour",
      ],
      selectedDistributionIntervalIndex: 0,
      raw_data: [],
      monthsOfYear: [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
      ],
      daysOfWeek: [
        "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"
      ],
      hoursOfDay: [
          "00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00",
          "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00",
          "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"
      ],
      stats: undefined,
      statsReady: false,
      termHeaders: [
        {
          text: 'Term',
          sortable: true,
          value: 'key'
        },
        {
          text: 'Count',
          sortable: true,
          value: 'doc_count'
        },
      ],
    }
  },
  computed: {
    selectedDistributionInterval() {
      return this.distributionIntervals[this.selectedDistributionIntervalIndex]
    },
    intervalChartOptions() {
      if (this.stats === undefined) return  {
        chart: {
          type: 'bar',
        },
      }

      let categories = []
      if (this.selectedDistributionInterval === "Year") {
        categories = []
        for (const entry of this.stats.year_histogram.buckets) {
          categories.push(entry.key)
        }
      } else if (this.selectedDistributionInterval === "Month") {
        categories = this.monthsOfYear
      } else if (this.selectedDistributionInterval === "Day") {
        categories = this.daysOfWeek
      } else if (this.selectedDistributionInterval === "Hour") {
        categories = this.hoursOfDay
      }

      return {
        chart: {
          type: 'bar',
        },
        xaxis: {
          labels: {
            show: true,
            hideOverlappingLabels: true
          },
          categories: categories
        },
      }
    },
    intervalChartSeries() {
      if (this.stats === undefined) return []

      let data = []

      switch (this.selectedDistributionInterval) {
        case "Year":
          data = Array(this.stats.year_histogram.length).fill(0)
          for (const [index, entry] of this.stats.year_histogram.buckets.entries()) {
            data[index] = entry.doc_count
          }
          break
        case "Month":
          data = Array(12).fill(0)
          for (const entry of this.stats.month_histogram.buckets) {
            data[entry.key - 1] = entry.doc_count
          }
          break
        case "Day":
          data = Array(7).fill(0)
          for (const entry of this.stats.day_histogram.buckets) {
            data[entry.key - 1] = entry.doc_count
          }
          break
        case "Hour":
          data = Array(24).fill(0)
          for (const entry of this.stats.hour_histogram.buckets) {
            data[entry.key] = entry.doc_count
          }
          break
        default:
          break
      }
      return [
        {
          name: 'Events by ' + this.selectedDistributionInterval,
          data: data
        }
      ]
    },
    fieldCardinality() {
      if (this.stats === undefined) return null
      return this.stats.all_values.field_cardinality.value
    },
    docCount() {
      if (this.stats === undefined) return null
      return this.stats.all_values.doc_count
    },
    fieldDateTimeMinimum() {
      if (this.stats === undefined) return null
      return this.stats.all_values.datetime_min.value_as_string
    },
    fieldDateTimeMaximum() {
      if (this.stats === undefined) return null
      return this.stats.all_values.datetime_max.value_as_string
    },
    valueDateTimeMinimum() {
      if (this.stats === undefined) return null
      return this.stats.datetime_min.value_as_string
    },
    valueDateTimeMaximum() {
      if (this.stats === undefined) return null
      return this.stats.datetime_max.value_as_string
    },
    fieldValueCount() {
      if (this.stats === undefined) return null
      return this.stats.all_values.field_count.value
    },
    valueEventCount() {
      if (this.stats === undefined) return null
      return this.stats.value_count.value
    },
    commonValues() {
      if (this.stats === undefined) return []
      return this.stats.all_values.top_terms.buckets
    },
    rareValues() {
      if (this.stats === undefined) return []
      return this.stats.all_values.rare_terms.buckets
    },
    donutChartOptions() {
      return {
        chart: {
          type: 'donut'
        },
        dataLabels: {
          enabled: true
        },
        labels: [this.eventValue + ' (' + this.valueEventCount + ')', 'Other ' + this.eventKey + ' (' + (this.fieldValueCount - this.valueEventCount) + ')'],
      }
    },
    donutChartSeries() {
      return [this.valueEventCount, this.fieldValueCount - this.valueEventCount]
    },
    minEvent: function() { return this.raw_data[0] },
    maxEvent: function() { return this.raw_data[this.raw_data.length - 1] },
    intervalHeatmapOptions() {
      return {
        chart: {
          type: 'heatmap',
        },
        colors: ["#008FFB"],
        tooltip: {
          enabled: true,
          x: { show: true },
        },
        xaxis: {
          labels: { show: true, hideOverlappingLabels: true },
          tickPlacement: "between",
        },
      }
    },
    intervalHeatmapSeries() {
      let series = []

      if (this.stats === undefined) return series

      for (let day of Array.from({ length: 7}).keys()) {
        let daySeries = []
        for (let hour of Array.from({ length: 24}).keys()) {
          const count = this.stats.hour_of_week_histogram.buckets[day*24 + hour].doc_count
          daySeries.push({x: this.hoursOfDay[hour], y: count})
        }
        series.push({ 'name': this.daysOfWeek[day], 'data': daySeries})
      }
      return series
    },
  },
  watch: {
    eventKey (value, oldValue) {
      if (value !== oldValue) {
          this.loadSummaryData()
        }
    },
    eventValue (value, oldValue){
      if (value !== oldValue) {
          this.loadSummaryData()
        }
    },
  },
  methods: {
    loadSummaryData: function() {
      this.statsReader = false
      this.stats = undefined
      this.raw_data = {}
      ApiClient.runAggregator(this.sketchId, {
        aggregator_name: 'field_summary',
        aggregator_parameters: {
          field: this.eventKey,
          field_query_string: this.eventValue
        }
      }).then((response) => {
        this.stats = response.data.objects[0].field_summary.buckets[0]
        this.statsReady = true
      })
    },
  },
  mounted() {
    this.loadSummaryData()
  }
}
</script>
