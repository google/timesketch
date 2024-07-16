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
  <v-container class="ma-0">
    <v-row>
      <v-col cols="12" md="12">
        <TsEventFieldSelect
          :field="selectedField"
          @selectedField="selectedField = $event"
          :rules="[rules.required]"
          >
          </TsEventFieldSelect>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-autocomplete
          outlined
          v-model="selectedAggregator"
          :disabled="disableAggregator"
          :items="aggregators"
          label="Aggregate events by"
          :rules="[rules.required]"
          append-icon="mdi-question"
        >
        <template #item="data">
          <v-tooltip bottom>
            <template #activator="{ on, attrs }">
              <v-layout wrap v-on="on" v-bind="attrs">
                <v-list-item-content>
                  <v-list-item-title>{{data.item.text}}</v-list-item-title>
                </v-list-item-content>
              </v-layout>
            </template>
            <span>{{ data.item.tooltip }}</span>
          </v-tooltip>
        </template>
        </v-autocomplete>
      </v-col>
    </v-row>
    <v-row v-if="!disableMetric" class="mt-n10">
      <v-col>
        <v-autocomplete
          outlined
          v-model="selectedMetric"
          :items="metrics"
          label="Aggregation Metric"
        ></v-autocomplete>
      </v-col>
    </v-row>
    <v-row v-if="!disableMaxItems" class="mt-n10">
      <v-col>
        <v-text-field
          :label="labelMaxItems"
          outlined
          v-model.number="selectedMaxItems"
          type="number"
          oninput="if(this.value < 1) this.value = 1;"
        />
      </v-col>
    </v-row>
    <v-row v-if="!disableInterval" class="mt-n10">
      <v-col>
        <v-autocomplete
          outlined
          v-model="selectedInterval"
          :items="allCalendarIntervals"
          label="Calendar interval"
        ></v-autocomplete>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import TsEventFieldSelect from './EventFieldSelect.vue'

export default {
  components: {
    TsEventFieldSelect,
  },
  props: {
    aggregator: {
      type: String,
    },
    field: {
      type: Object,
    },
    interval: {
      type: Object,
    },
    intervalQuantity: {
      type: Number,
    },
    maxItems: {
      type: Number,
    },
    metric: {
      type: String,
    },
    splitByTimeline: {
      type: Boolean,
    },
  },
  data() {
    return {
      enableCalendarInterval: false,
      selectedAggregator: this.aggregator,
      selectedField: this.field,
      selectedInterval: this.interval,
      selectedIntervalQuantity: this.intervalQuantity,
      selectedMaxItems: this.maxItems,
      selectedMetric: this.metric,
      selectedSplitByTimeline: this.splitByTimeline,
      rules: {
          required: value => !!value || 'Required.',
      },
      intMetrics: [
        {
          text: 'Average',
          value: 'avg'
        },
        {
          text: 'Count',
          value: 'value_count'
        },
        {
          text: 'Minimum',
          value: 'min'
        },
        {
          text: 'Maximum',
          value: 'max'
        },
        {
          text: 'Sum',
          value: 'sum'
        },
        {
          text: 'Unique',
          value: 'cardinality'
        },
      ],
      stringAggregators: [
        {
          text: 'Auto Date Histogram',
          value: 'auto_date_histogram',
          tooltip: 'Aggregates events into a set number of intervals by datetime.'
        },
        {
          text: 'Rare Terms',
          value: 'rare_terms',
          tooltip: 'Aggregates by unique and infrequent terms.'
        },
        // { text: 'Significant terms', value: 'significant_terms' }, // podium-gold
        {
          text: 'Date Histogram',
          value: 'calendar_date_histogram',
          tooltip: 'Aggregates events by calendar intervals.'
        },
        {
          text: 'Top Terms',
          value: 'top_terms',
          tooltip: 'Aggregates by the most common and unique terms.'
        },
      ],
      allAggregators: [
        {
          text: 'Auto Date Histogram',
          value: 'auto_date_histogram',
          tooltip: 'Aggregates events into a set number of intervals by datetime.'
        },
        {
          text: 'Rare terms',
          value: 'rare_terms',
          tooltip: 'Aggregates by unique and infrequent terms.'
        },
        // { text: 'Significant terms', value: 'significant_terms' }, // podium-gold
        // {
        //   text: 'Single Metric',
        //   value: 'single_metric'
        // },
        {
          text: 'Date Histogram',
          value: 'calendar_date_histogram',
          tooltip: 'Aggregates events by calendar intervals.'
        },
        {
          text: 'Top Terms',
          value: 'top_terms',
          tooltip: 'Aggregates by the most common and unique terms.'
        },
      ],
      stringMetrics: [
        {
          text: 'Count',
          value: 'value_count'
        },
        {
          text: 'Unique', value: 'cardinality'
        },
      ],
      allCalendarIntervals: [
        {
          text: 'Year',
          value: {
            interval: 'year',
            max: 10,
          }
        },
        {
          text: 'Quarter',
          value: {
            interval: 'quarter',
            max: 4
          }
        },
        {
          text: 'Month',
          value: {
            interval: 'month',
            max: 12
          }
        },
        {
          text: 'Week',
          value: {
            interval: 'week',
            max: 52
          }
        },
        {
          text: 'Day',
          value: {
            interval: 'day',
            max: 31
          }
        },
        {
          text: 'Hour',
          value: {
            interval: 'hour',
            max: 24
          }
        },
        {
          text: 'Minute',
          value: {
            interval: 'minute',
            max: 60
          }
        },
      ],
    }
  },
  computed: {
    labelMaxItems() {
      if (this.selectedAggregator === "rare_terms") {
        return "Maximum document count for rare items"
      } else if (this.selectedAggregator === "auto_date_histogram") {
        return "Maximum number of intervals"
      }
      return "Maximum number of items (K)"
    },
    aggregators() {
      if (this.selectedField == null) {
        return []
      }

      if (this.selectedField.type === 'text') {
        return this.stringAggregators
      }

      return this.allAggregators
    },
    disableAggregator() {
      return this.selectedField == null
    },
    disableInterval() {
      return !(
        this.selectedAggregator &&
        this.selectedAggregator === 'calendar_date_histogram'
      )
    },
    disableTimelineSplit() {
      return !(
        this.selectedAggregator &&
        this.selectedAggregator.endsWith('date_histogram'))
    },
    disableMaxItems() {
      return !(
        this.selectedAggregator && (
          this.selectedAggregator === 'top_terms' ||
          this.selectedAggregator === 'significant_terms' ||
          this.selectedAggregator === 'auto_date_histogram' ||
          this.selectedAggregator === 'rare_terms'
        )
      )
    },
    disableMetric() {
      return !(
        this.selectedAggregator && (
          this.selectedAggregator === 'auto_date_histogram' ||
          this.selectedAggregator === 'calendar_date_histogram' ||
          this.selectedAggregator === 'single_metric'
        )
      )
    },
    metrics() {
      if (this.selectedField == null)
        return []

      if (this.selectedField.type === 'text') {
        return this.stringMetrics
      }
      else {
        return this.intMetrics
      }
    },
    intervalQuantities() {
      if (this.selectedInterval == null) {
        return []
      }
      return [...Array(this.selectedInterval.max - 1).keys()].map((_, i) => i + 1)
    },
  },
  watch: {
    aggregator() {
      this.selectedAggregator = this.aggregator
      if (this.selectedAggregator === 'top_terms' || this.selectedAggregator === 'rare_terms') {
        this.selectedMetric = 'value_count'
      } else if (this.selectedMetric == null) {
        this.selectedMetric = 'value_count'
      }
    },
    field() {
      this.selectedField = this.field
    },
    interval() {
      this.selectedInterval = this.interval
    },
    intervalQuantity() {
      this.selectedIntervalQuantity = this.intervalQuantity
    },
    maxItems() {
      this.selectedMaxItems = this.maxItems
    },
    metric() {
      this.selectedMetric = this.metric
    },
    selectedAggregator() {
      this.$emit('updateAggregator', this.selectedAggregator)
    },
    selectedField() {
      this.$emit('updateField', this.selectedField)
    },
    selectedInterval() {
      this.$emit('updateInterval', this.selectedInterval)
    },
    selectedIntervalQuantity() {
      this.$emit('updateIntervalQuantity', this.selectedIntervalQuantity)
    },
    selectedMaxItems() {
      this.$emit('updateMaxItems', this.selectedMaxItems)
    },
    selectedMetric() {
      this.$emit('updateMetric', this.selectedMetric)
    },
    selectedSplitByTimeline() {
      this.$emit('updateSplitByTimeline', this.splitByTimeline)
    },
  }
}
</script>
