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
  <v-card width="700" style="overflow: visible">
    <v-container class="px-8">
      <br />

      <v-row>
        <v-col cols="12">
          <v-btn class="mr-2" size="small" variant="tonal" @click="getDateRange(0, 'days')">Today</v-btn>
          <v-btn class="mr-2" size="small" variant="tonal" @click="getDateRange(7, 'days')">Last 7 days</v-btn>
          <v-btn class="mr-2" size="small" variant="tonal" @click="getDateRange(30, 'days')">Last 30 days</v-btn>
          <v-btn class="mr-2" size="small" variant="tonal" @click="getDateRange(90, 'days')">Last 90 days</v-btn>
          <v-btn class="mr-2" size="small" variant="tonal" @click="getDateRange(1, 'year')">Last 1 year</v-btn>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="6">
          <v-text-field
            :model-value="formatStartTime"
            label="From"
            variant="outlined"
            hide-details
            v-on:click="showPicker = true"
            @blur="setStartTimeFromEvent"
            @keydown.enter="setStartTimeFromEvent"
          >
          </v-text-field>
        </v-col>
        <v-col cols="6">
          <v-text-field
            :model-value="formatEndTime"
            label="To (optional)"
            variant="outlined"
            hide-details
            v-on:click="showPicker = true"
            @blur="setEndTimeFromEvent"
            @keydown.enter="setEndTimeFromEvent"
            :append-outer-icon="showPicker ? 'mdi-calendar-remove' : 'mdi-calendar'"
            @click:append-outer="showPicker = !showPicker"
          >
          </v-text-field>
        </v-col>
      </v-row>

      <v-row v-if="showPicker">
        <v-col cols="12">
          <date-picker
            v-model.range="dateRange"
            mode="dateTime"
            ref="picker"
            timezone="UTC"
            :is-dark="$vuetify.theme.dark"
            is24hr
            :expanded="true"
          ></date-picker>
        </v-col>
      </v-row>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="clearAndCancel"> Cancel </v-btn>
        <v-btn variant="text" color="primary" @click="submit()"> Add filter </v-btn>
      </v-card-actions>
    </v-container>
  </v-card>
</template>

<script>
import dayjs from '@/plugins/dayjs'

import { DatePicker } from 'v-calendar';
import 'v-calendar/style.css';

export default {
  props: ['selectedChip'],
  components: {
    DatePicker,
  },
  data() {
    return {
      range: {
        start: '',
        end: '',
      },
      filterTab: null,
      showPicker: false,
    }
  },
  computed: {
    dateRange: {
      set(val) {
        if (val && val.start && val.end) {
          this.range.start = dayjs.utc(val.start).millisecond(0).toISOString()
          this.range.end = dayjs.utc(val.end).millisecond(0).toISOString()
        } else {
          this.range.start = ''
          this.range.end = ''
        }
      },
      get() {
        let range = {
          start: this.range.start,
          end: this.range.end,
        }
        return range
      },
    },
    formatStartTime: function () {
      return this.range.start
    },
    formatEndTime: function () {
      if (this.range.start === this.range.end || !this.range.start) {
        return ''
      }
      return this.range.end
    },
  },
  created() {
    if (this.selectedChip) {
      this.range.start = this.selectedChip.value.split(',')[0]
      this.range.end = this.selectedChip.value.split(',')[1]
    }
  },
  methods: {
    getDateRange: function (num, resolution) {
      let now = dayjs.utc()
      let then = now.subtract(num, resolution)
      let chipType = 'datetime_range'
      let chipValue = then.format('YYYY-MM-DD') + ',' + now.format('YYYY-MM-DD')
      let chip = {
        field: '',
        type: chipType,
        value: chipValue,
        operator: 'must',
        active: true,
      }
      this.addChip(chip)
      this.$emit('cancel')

      return { start: now, end: then }
    },

    setStartTimeFromEvent: function(event) {
      const newValue = event.target.value;
      this.setStartTime(newValue);
    },
    setStartTime: function (newDateTime) {
      if (!newDateTime) {
        this.range.start = ''
        return
      }
      this.range.start = dayjs.utc(newDateTime).toISOString()
      if (!this.range.end) {
        if (this.range.start) {
          this.range.end = this.range.start || ''
        }
      }
      this.$refs.picker.move(this.range.start)
    },
    setEndTimeFromEvent: function(event) {
      const newValue = event.target.value;
      this.setEndTime(newValue);
    },
    setEndTime: function (newDateTime) {
      if (!newDateTime) {
        this.range.end = ''
        return
      }
      this.range.end = dayjs.utc(newDateTime).toISOString()
      this.$refs.picker.move(this.range.end)
    },
    addDateTimeChip: function (chipValue) {
      const chipType = 'datetime_range'
      let chip = {
        field: '',
        type: chipType,
        value: chipValue,
        operator: 'must',
        active: true,
      }
      this.addChip(chip)
      this.range = {
        start: null,
        end: null,
      }
    },
    clearAndCancel: function () {
      this.range = {
        start: '',
        end: '',
      }
      this.$emit('cancel')
    },
    addChip: function (newChip) {
      if (this.selectedChip) {
        this.$emit('updateChip', newChip)
      } else {
        this.$emit('addChip', newChip)
      }
    },
    submit: function () {
      if (!this.range.start) {
        return
      }

      if (this.range.start === this.range.end) {
        let dateTimeArray = this.range.start.split('T')
        let date = dateTimeArray[0]
        let chipValue = date + ',' + date
        this.addDateTimeChip(chipValue)
      }

      if (this.range.start !== this.range.end) {
        let chipType = 'datetime_range'
        let chipValue = this.range.start + ',' + this.range.end
        let chip = {
          field: '',
          type: chipType,
          value: chipValue,
          operator: 'must',
          active: true,
        }
        this.addChip(chip)
        this.range = {
          start: '',
          end: '',
        }
      }

      this.$emit('cancel')
    },
  },
}
</script>

<style scoped lang="scss"></style>
