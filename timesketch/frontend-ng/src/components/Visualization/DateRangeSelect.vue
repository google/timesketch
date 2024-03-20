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
  <v-container fluid class="ma-0 pa-0">
    <v-row>
      <v-col>
        <v-btn class="mr-2" small depressed @click="getDateRange(1, 'days')">
          Last 24 hours
        </v-btn>
        <v-btn class="mr-2" small depressed @click="getDateRange(7, 'days')">
          Last 7 days
        </v-btn>
        <v-btn class="mr-2" small depressed @click="getDateRange(30, 'days')">
          Last 30 days
        </v-btn>
        <v-btn class="mr-2" small depressed @click="getDateRange(90, 'days')">
          Last 90 days
        </v-btn>
        <v-btn class="mr-2" small depressed @click="getDateRange(1, 'year')">
          Last 1 year
        </v-btn>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="6">       
        <v-text-field
          :value="formatStartTime"
          label="From"
          outlined
          hide-details
          :dense="isDense"
          v-on:click="showPicker = true"
          v-on:change="setStartTime"
          @input="$emit('change', dateRange)"
        >
        </v-text-field>
      </v-col>
      <v-col cols="6">
        <v-text-field
          :value="formatEndTime"
          label="To (optional)"
          outlined
          hide-details
          :dense="isDense"
          v-on:click="showPicker = true"
          v-on:change="setEndTime"
          :append-outer-icon="showPicker ? 'mdi-calendar-remove' : 'mdi-calendar'"
          @click:append-outer="showPicker = !showPicker"
          @input="$emit('change', dateRange)"
        >
        </v-text-field>
      </v-col>
    </v-row>
    <v-row v-if="showPicker">
      <v-col>
        <date-picker
          v-model="dateRange"
          mode="dateTime"
          ref="picker"
          timezone="UTC"
          :is-dark="$vuetify.theme.dark"
          is24hr
          is-range
          is-expanded
        ></date-picker>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import dayjs from '@/plugins/dayjs'
import DatePicker from 'v-calendar/lib/components/date-picker.umd'

export default {
  components: {
    DatePicker,
  },
  props: {
    range: {
      type: Object,
      default: function() {
        return { 
          start: '', 
          end: ''
        }
      },
    },
    isDense: { 
      type: Boolean, 
      default: false 
    },
  },
  data() {
    return {
      selectedRange: {
        start: this.range.start,
        end: this.range.end,
      },
      showPicker: false, 
    }
  },
  methods: {
    clearRange: function () {
      this.selectedRange = { 
        start: '', 
        end: '' 
      }
    },
    getDateRange: function (num, resolution) {
      let now = dayjs.utc()
      let then = now.subtract(num, resolution)

      this.selectedRange = { 
        start: then.millisecond(0).toISOString(), 
        end: now.millisecond(0).toISOString() 
      }
      this.$emit('change', this.selectedRange)
    },
    setStartTime: function (newDateTime) {
      if (!newDateTime) {
        this.selectedRange.start = ''
        return
      }
      this.selectedRange.start = dayjs.utc(newDateTime).toISOString()
      if (!this.selectedRange.end) {
        if (this.selectedRange.start) {
          this.selectedRange.end = this.selectedRange.start || ''
        }
      }
      this.$refs.picker.focusDate(this.selectedRange.start)
      this.$emit('change', this.dateRange)
    },
    setEndTime: function (newDateTime) {
      if (!newDateTime) {
        this.selectedRange.end = ''
        return
      }
      this.selectedRange.end = dayjs.utc(newDateTime).toISOString()
      this.$refs.picker.focusDate(this.selectedRange.start)
      this.$emit('change', this.dateRange)
    },
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    dateRange: {
      set(val) {
        this.selectedRange.start = dayjs.utc(val.start).millisecond(0).toISOString()
        this.selectedRange.end = dayjs.utc(val.end).millisecond(0).toISOString()
        this.$emit('change', this.selectedRange)
      },
      get() {
        let range = {
          start: this.selectedRange.start,
          end: this.selectedRange.end,
        }
        return range
      },
    },
    formatStartTime: function () {
      return this.selectedRange.start
    },
    formatEndTime: function () {
      if (
        this.selectedRange.start === this.selectedRange.end || 
        !this.selectedRange.start) {
        return ''
      }
      return this.selectedRange.end
    },
  },
  watch: {
    range() {
      this.selectedRange = this.range
    }
  }
}
</script>
