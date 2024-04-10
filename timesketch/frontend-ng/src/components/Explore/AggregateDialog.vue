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
  <v-card class="mx-auto" >
    <v-toolbar dense flat>
      <h3 class="ml-6" style="white-space: nowrap;">Event Data Analytics</h3>
      <div>
        <v-chip outlined class="ml-2">Field:&nbsp;<span style="font-family: monospace">{{ this.eventKey }}</span></v-chip>
        <v-chip outlined class="ml-2">Value:&nbsp;<span style="font-family: monospace">{{ this.truncateValue(this.eventValue)  }}</span></v-chip>
        <v-chip outlined class="ml-2">Event datetime:&nbsp;<span style="font-family: monospace">{{ this.eventDateTime }}</span></v-chip>
      </div>
      <v-spacer></v-spacer>
      <v-btn icon @click="clearAndCancel">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-toolbar>
    <v-card-text>
      <v-container fluid >
        <v-row justify="center">
          <v-col>
            <v-card outlined height="146px" :loading="!statsReady">
              <v-card-title>
                Sketch statistics
              </v-card-title>
              <v-simple-table dense v-if="statsReady" class="px-2 mt-n4">
                <tbody>
                  <tr>
                    <td width="200px">Total number of events</td>
                    <td><strong>{{ this.formatNumber(this.docCount) }}</strong></td>
                  </tr>
                  <tr>
                    <td width="200px">First event</td>
                    <td style="white-space: nowrap;"><strong>{{ this.fieldDateTimeMinimum }}</strong></td>
                  </tr>
                  <tr>
                    <td width="200px">Last event</td>
                    <td><strong>{{ this.fieldDateTimeMaximum }}</strong></td>
                  </tr>
                </tbody>
              </v-simple-table>
            </v-card>
            <v-card outlined height="146px" :loading="!statsReady" class="mt-1">
              <v-card-title>
                Field statistics
              </v-card-title>
              <v-simple-table dense v-if="statsReady" class="px-2 mt-n4">
                <tbody>
                  <tr>
                    <td width="200px">Field name</td>
                    <td><span style="font-family: monospace">{{ this.eventKey }}</span></td>
                  </tr>
                  <tr>
                    <td width="200px">Total number of events</td>
                    <td><strong>{{ this.fieldValueCount }}</strong></td>
                  </tr>
                  <tr>
                    <td width="200px">Number of unique values</td>
                    <td><strong>{{ this.fieldCardinality }}</strong></td>
                  </tr>
                </tbody>
              </v-simple-table>
            </v-card>
            <v-card outlined height="180px" :loading="!statsReady" class="mt-1">
              <v-card-title>
                Value statistics
              </v-card-title>
              <v-simple-table dense v-if="statsReady" class="px-2 mt-n4">
                <tbody>
                  <tr>
                    <td width="200px">Field value</td>
                    <td><span style="font-family: monospace">{{ this.eventValue }}</span></td>
                  </tr>
                  <tr>
                    <td width="200px">Total number of events</td>
                    <td><strong>{{ this.valueEventCount }}</strong></td>
                  </tr>
                  <tr>
                    <td width="200px">First event</td>
                    <td><strong>{{ this.valueDateTimeMinimum }}</strong></td>
                  </tr>
                  <tr>
                    <td width="200px">Last event</td>
                    <td><strong>{{ this.valueDateTimeMaximum }}</strong></td>
                  </tr>
                </tbody>
              </v-simple-table>
            </v-card>
          </v-col>
          <v-col align="center">
              <v-card outlined height="480px" :loading="!statsReady">
                <v-card-title>
                  Top {{ Math.min(10, this.commonValues.length) }} &nbsp;<span style="font-family: monospace">{{ eventKey }}</span>&nbsp; values
                  <v-spacer></v-spacer>
                  <v-tooltip bottom>
                    <template v-slot:activator="{ on }">
                      <v-icon color="primary" v-on="on">mdi-information-outline</v-icon>
                    </template>
                    <span>The top {{ Math.min(10, this.commonValues.length) }} most common
                      &nbsp;<span style="font-family: monospace">{{ eventKey }}</span>&nbsp; values
                      (out of {{ this.fieldCardinality }} unique values).
                    </span>
                  </v-tooltip>
                </v-card-title>
                <v-card-text>
                  <v-data-table
                    :headers="termHeaders"
                    :items="commonValues"
                    :items-per-page="10"
                    :hide-default-footer="(commonValues.length <= 10)"
                    dense
                  >
                  </v-data-table>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col align="center">
              <v-card outlined height="480px" :loading="!statsReady">
                <v-card-title>
                  Rare &nbsp;<span style="font-family: monospace">{{ eventKey }}</span>&nbsp; values
                  <v-spacer></v-spacer>
                  <v-tooltip bottom>
                    <template v-slot:activator="{ on }">
                      <v-icon color="primary" v-on="on">mdi-information-outline</v-icon>
                    </template>
                    <span>Rare &nbsp;<span style="font-family: monospace">{{ eventKey }}</span>&nbsp;
                      events that have a maximum event count of 5
                    </span>
                  </v-tooltip>
                </v-card-title>
                <v-card-text>
                  <v-data-table
                    :headers="termHeaders"
                    :items="rareValues"
                    :items-per-page="10"
                    :hide-default-footer="(rareValues.length <= 10)"
                    :footer-props="{
                      disableItemsPerPage: true
                    }"
                    dense
                  >
                  </v-data-table>
                </v-card-text>
              </v-card>
            </v-col>
        </v-row>
        <v-row>
          <v-col align="center">
            <v-card outlined height="480px" :loading="!statsReady">
              <v-card-title>
                Percentage of &nbsp;<span style="font-family: monospace">{{ eventKey }}</span>&nbsp; events
                <v-spacer></v-spacer>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on }">
                    <v-icon color="primary" v-on="on">mdi-information-outline</v-icon>
                  </template>
                  <span>Shows the ratio of <span style="font-family: monospace">{{ this.truncateValue(eventValue) }}</span>
                    events to other <span style="font-family: monospace">{{ eventKey }}</span> events.
                  </span>
                </v-tooltip>
              </v-card-title>
              <v-card-text v-if="statsReady">
                <apexchart
                  height="350px"
                  :options="this.donutChartOptions"
                  :series="this.donutChartSeries"
                ></apexchart>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col align="center">
            <v-card outlined height="480px" :loading="!eventDistributionReady">
              <v-card-title>
                Event distribution by {{ this.distributionIntervals[this.selectedDistributionIntervalIndex] }}
                <v-spacer></v-spacer>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on }">
                    <v-icon color="primary" v-on="on">mdi-information-outline</v-icon>
                  </template>
                  <span>Shows the distribution of <span style="font-family: monospace">{{ this.truncateValue(eventValue) }}</span>
                    events in the sketch based on the {{ this.distributionIntervals[this.selectedDistributionIntervalIndex] }}
                    of the datetime.
                  </span>
                </v-tooltip>
              </v-card-title>
              <v-card-text v-if="statsReady">
                <v-btn-toggle mandatory v-model="selectedDistributionIntervalIndex">
                  <v-btn v-for="interval in this.distributionIntervals" :key="interval" small>
                    {{ interval }}
                  </v-btn>
                </v-btn-toggle>
                <apexchart
                  height="350px"
                  :options="this.intervalChartOptions"
                  :series="this.intervalChartSeries"
                ></apexchart>
              </v-card-text>
            </v-card>
          </v-col>

            <v-col align="center">
            <v-card outlined height="480" :loading="!dataReady">
              <v-card-title>
                Surrounding events
                <v-spacer></v-spacer>
                <v-tooltip bottom>
                  <template v-slot:activator="{ on }">
                    <v-icon color="primary" v-on="on">mdi-information-outline</v-icon>
                  </template>
                  <span>Shows the distribution of <span style="font-family: monospace">{{ this.truncateValue(eventValue) }}</span>
                    events that are {{ this.recentIntervals[this.selectedRecentEventsIndex] }} of
                    <span style="font-family: monospace">{{ eventDateTime }}</span>
                  </span>
                </v-tooltip>
              </v-card-title>
              <v-card-text v-if="dataReady">
                <v-btn-toggle mandatory v-model="selectedRecentEventsIndex">
                  <v-btn v-for="interval in this.recentIntervals" :key="interval" small>
                    {{ interval }}
                  </v-btn>
                </v-btn-toggle>
                <apexchart
                  height="350px"
                  :options="this.recentHistogramOptions"
                  :series="this.recentHistogramSeries"
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
    'reloadData',
  ],
  data() {
    return {
      distributionIntervals: [
        "Year",
        "Month",
        "Day",
        "Hour",
        "Hour-Day",
      ],
      recentIntervals: [
        "± 5 years",
        "± 6 months",
        "± 7 days",
        "± 6 hours",
      ],
      recentHistogramLabels: [],
      recentHistogramSeries: [],
      selectedDistributionIntervalIndex: 0,
      selectedRecentEventsIndex: 2,
      dataReady: false,
      data: [],
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
      eventDistributionReady: false,
      eventDistributionData: undefined,
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
    sketch() {
      return this.$store.state.sketch
    },
    eventDateTime() {
      return new Date(this.eventTimestamp).toISOString()
    },
    selectedDistributionInterval() {
      return this.distributionIntervals[this.selectedDistributionIntervalIndex]
    },
    selectedRecentEvents() {
      return this.recentIntervals[this.selectedRecentEventsIndex]
    },
    intervalChartOptions() {
      if (this.eventDistributionData === undefined || !this.eventDistributionReady) return  {
        chart: {
          type: 'bar',
        },
      }

      let categories = []
      if (this.selectedDistributionInterval === "Year") {
        categories = []
        for (const entry of this.eventDistributionData.year_histogram.buckets) {
          categories.push(entry.key)
        }
      } else if (this.selectedDistributionInterval === "Month") {
        categories = this.monthsOfYear
      } else if (this.selectedDistributionInterval === "Day") {
        categories = this.daysOfWeek
      } else if (this.selectedDistributionInterval === "Hour") {
        categories = this.hoursOfDay
      } else if (this.selectedDistributionInterval === "Hour-Day") {
        return this.intervalHeatmapOptions
      }
      return {
        chart: {
          type: 'bar',
        },
        xaxis: {
          tickAmount: 12,
          labels: {
            show: true,
            hideOverlappingLabels: true
          },
          categories: categories
        },
      }
    },
    intervalChartSeries() {
      if (this.eventDistributionData === undefined || !this.eventDistributionReady) return []

      let data = []

      switch (this.selectedDistributionInterval) {
        case "Year":
          data = Array(this.eventDistributionData.year_histogram.length).fill(0)
          for (const [index, entry] of this.eventDistributionData.year_histogram.buckets.entries()) {
            data[index] = entry.doc_count
          }
          break
        case "Month":
          data = Array(12).fill(0)
          for (const entry of this.eventDistributionData.month_histogram.buckets) {
            data[entry.key - 1] = entry.doc_count
          }
          break
        case "Day":
          data = Array(7).fill(0)
          for (const entry of this.eventDistributionData.day_histogram.buckets) {
            data[entry.key] = entry.doc_count
          }
          break
        case "Hour":
          data = Array(24).fill(0)
          for (const entry of this.eventDistributionData.hour_histogram.buckets) {
            data[entry.key] = entry.doc_count
          }
          break
        case "Hour-Day":
          return this.intervalHeatmapSeries
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
        labels: [
          this.truncateValue(this.eventValue)  + ' (' + this.valueEventCount + ')',
          'Other ' + this.eventKey + ' (' +
            (this.fieldValueCount - this.valueEventCount) + ')'
        ],
        legend: {
          position: 'bottom'
        },
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
          categories: this.hoursOfDay,
        },
      }
    },
    intervalHeatmapSeries() {
      let series = []

      if (this.eventDistributionData === undefined) return series

      for (let day of Array.from({ length: 7}).keys()) {
        let daySeries = []
        for (let hour of Array.from({ length: 24}).keys()) {
          const count = this.eventDistributionData.hour_of_week_histogram.buckets[day*24 + hour].doc_count
          daySeries.push({x: this.hoursOfDay[hour], y: count})
        }
        series.push({ 'name': this.daysOfWeek[day], 'data': daySeries})
      }
      return series
    },
    recentHistogramOptions() {
      if (!this.dataReady) return  {
        chart: {
          type: 'bar',
        },
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
          categories: this.recentHistogramLabels
        },
      }
    },
  },
  watch: {
    reloadData (value, oldValue) {
      if (value === true) {
        this.loadSummaryData()
        this.loadEventDistribution()
        this.loadAggregationData()
      }
    },
    selectedDistributionInterval (value, oldValue) {
      if (value !== oldValue) {
        this.loadEventDistribution()
      }
    },
    selectedRecentEvents (value, oldValue) {
      if (value !== oldValue) {
        this.loadAggregationData()
      }
    }
  },
  methods: {
    truncateValue(value) {
      if (value.length > 45) {
        return value.substring(0, 45).trim() + '...'
      }
      return value
    },
    formatNumber(number) {
      return new Intl.NumberFormat().format(number)
    },
    loadSummaryData: function() {
      this.statsReady = false
      this.stats = undefined
      ApiClient.runAggregator(this.sketch.id, {
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
    loadEventDistribution: function() {
      this.eventDistributionReady = false
      this.eventDistributionData = []
      ApiClient.runAggregator(this.sketch.id, {
        aggregator_name: 'datefield_summary',
        aggregator_parameters: {
          field: this.eventKey,
          date_interval: this.selectedDistributionInterval
        }
      }).then((response) => {
        this.eventDistributionData = response.data.objects[0].datefield_summary.buckets[0]
        this.eventDistributionReady = true
      })
    },
    loadAggregationData: function() {
      this.dataReady = false
      this.data = []

      const currentDateTime = new Date(this.eventTimestamp/1000)
      let startTime, endTime
      let supportedIntervals

      switch (this.selectedRecentEvents) {
        case "± 5 years":
          startTime = new Date(this.eventTimestamp/1000)
          startTime.setUTCFullYear(currentDateTime.getUTCFullYear() - 5)
          endTime = new Date(this.eventTimestamp/1000)
          endTime.setUTCFullYear(currentDateTime.getUTCFullYear() + 5)
          supportedIntervals = "year"
          break
        case "± 6 months":
          startTime = new Date(this.eventTimestamp/1000)
          startTime.setUTCMonth(currentDateTime.getUTCMonth() - 6)
          endTime = new Date(this.eventTimestamp/1000)
          endTime.setUTCMonth(currentDateTime.getUTCMonth() + 6)
          supportedIntervals = "month"
          break
        case "± 7 days":
          startTime = new Date(this.eventTimestamp/1000)
          startTime.setUTCDate(currentDateTime.getUTCDate() - 7)
          endTime = new Date(this.eventTimestamp/1000)
          endTime.setUTCDate(currentDateTime.getUTCDate() + 7)
          supportedIntervals = "day"
          break
        case "± 6 hours":
          startTime = new Date(this.eventTimestamp/1000)
          startTime.setUTCHours(currentDateTime.getUTCHours() - 6)
          endTime = new Date(this.eventTimestamp/1000)
          endTime.setUTCHours(currentDateTime.getUTCHours() + 6)
          supportedIntervals = "hour"
          break
        default:
          return
      }
      ApiClient.runAggregator(this.sketch.id, {
        aggregator_name: 'date_histogram',
        aggregator_parameters: {
          field: this.eventKey,
          field_query_string: this.eventValue,
          supported_intervals: supportedIntervals,
          start_time: startTime.toISOString().slice(0, -1),
          end_time: endTime.toISOString().slice(0, -1),
        }
      }).then((response) => {
        this.data = response.data.objects[0].date_histogram.buckets[0]
        this.recentHistogramSeries = [{
          data: [],
          name: 'Events'
        }]
        this.recentHistogramLabels = []

        for (const [index, entry] of response.data.objects[0].date_histogram.buckets[0].entries()) {
          this.recentHistogramSeries[0].data[index] = entry.count
          this.recentHistogramLabels[index] = entry.datetime.slice(0, -5)
        }
        this.dataReady = true
      })
    },
    clearAndCancel: function() {
      this.$emit('cancel')
    },
  },
  mounted() {
    this.loadSummaryData()
    this.loadEventDistribution()
    this.loadAggregationData()
  }
}
</script>
