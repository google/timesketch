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
  <v-card width="700">
    <v-toolbar flat>
      <v-tabs centered grow v-model="filterTab">
        <v-tab> Time filter </v-tab>
        <v-tab> Field filter </v-tab>
      </v-tabs>
    </v-toolbar>
    <v-tabs-items v-model="filterTab">
      <v-tab-item :transition="false">
        <v-container class="px-8">
          <br>

          <v-row>
            <v-col cols="12">
            <v-btn class="mr-2" small depressed @click="getDateRange(0, 'days')">Today</v-btn>
            <v-btn class="mr-2" small depressed @click="getDateRange(7, 'days')">Last 7 days</v-btn>
            <v-btn class="mr-2" small depressed @click="getDateRange(30, 'days')">Last 30 days</v-btn>
            <v-btn class="mr-2" small depressed @click="getDateRange(90, 'days')">Last 90 days</v-btn>
            <v-btn class="mr-2" small depressed @click="getDateRange(1, 'year')">Last 1 year</v-btn>
            </v-col>
          </v-row>

          <br>

          <h5>Single day</h5>
          <v-row>
            <v-col cols="12">
              <v-menu transition="scale-transition" offset-y min-width="auto">
                <template v-slot:activator="{ on, attrs }">
                  <v-text-field v-model="singleDate" label="Single day" v-bind="attrs" v-on="on">{{
                    singleDate
                  }}</v-text-field>
                </template>
                <v-date-picker v-model="singleDate" no-title> </v-date-picker>
              </v-menu>
            </v-col>
          </v-row>

          <br>

          <h5>Timerange</h5>
          <v-row>
            <v-col cols="3">
              <v-menu transition="scale-transition" offset-y min-width="auto">
                <template v-slot:activator="{ on, attrs }">
                  <v-text-field v-model="timerange.startDate" label="Start date" v-bind="attrs" v-on="on">{{
                    timerange.startDate
                  }}</v-text-field>
                </template>
                <v-date-picker v-model="timerange.startDate" no-title> </v-date-picker>
              </v-menu>
            </v-col>

            <v-col cols="2">
              <v-menu transition="scale-transition" offset-y min-width="auto" :close-on-content-click="false">
                <template v-slot:activator="{ on, attrs }">
                  <v-text-field v-model="timerange.startTime" label="Start time" v-bind="attrs" v-on="on">{{
                    timerange.startTime
                  }}</v-text-field>
                </template>

                <v-time-picker v-model="timerange.startTime" format="24hr" use-seconds> </v-time-picker>
              </v-menu>
            </v-col>

            <v-col cols="2">
              <v-icon class="mt-5 ml-8">mdi-arrow-right-thin</v-icon>
            </v-col>

            <v-col cols="3">
              <v-menu transition="scale-transition" offset-y min-width="auto">
                <template v-slot:activator="{ on, attrs }">
                  <v-text-field v-model="timerange.endDate" label="End date" v-bind="attrs" v-on="on">{{ timerange.endDate }}</v-text-field>
                </template>

                <v-date-picker v-model="timerange.endDate" no-title> </v-date-picker>
              </v-menu>
            </v-col>
            <v-col cols="2">
              <v-menu transition="scale-transition" offset-y min-width="auto" :close-on-content-click="false">
                <template v-slot:activator="{ on, attrs }">
                  <v-text-field v-model="timerange.endTime" label="End time" v-bind="attrs" v-on="on">{{ timerange.endTime }}</v-text-field>
                </template>
                <v-time-picker v-model="timerange.endTime" format="24hr" use-seconds> </v-time-picker>
              </v-menu>
            </v-col>

          </v-row>

          <br>

          <h5>Datetime string</h5>
          <v-row dense>

            <v-col cols="5">
                  <v-text-field v-model="startDate" label="Datetime string"></v-text-field>
            </v-col>
            <v-col cols="2">
              <v-icon class="mt-5 ml-10">mdi-arrow-right-thin</v-icon>
            </v-col>
            <v-col cols="5">
                  <v-text-field v-model="startDate" label="(Optional) Make it a timerange"></v-text-field>
            </v-col>

          </v-row>

          <v-card class="pa-4" >
          <h5>Create a timerange</h5>
          <br>
          <v-row>
            <v-col cols="2">
              <v-text-field prepend-inner-icon="mdi-minus" dense placeholder="5"></v-text-field>
            </v-col>
            <v-col cols="2">
              <v-text-field prepend-inner-icon="mdi-plus" dense placeholder="5"></v-text-field>
            </v-col>

            <v-col cols="4">
              <v-select
                dense
                value="Minutes"
                :items="['Seconds', 'Minutes', 'Hours', 'Days']"
                outlined
              ></v-select>
            </v-col>
          </v-row>
          </v-card>


          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn text color="primary" @click="$emit('cancel')"> Cancel </v-btn>
            <v-btn text color="primary" @click="submit()"> Add filter </v-btn>
          </v-card-actions>
        </v-container>
      </v-tab-item>
      <v-tab-item :transition="false">
        <v-container class="px-8">Not implemented yet</v-container>
      </v-tab-item>
    </v-tabs-items>
  </v-card>
</template>

<script>
import dayjs from '@/plugins/dayjs'

export default {
  data() {
    return {
      singleDate: null,
      timerange: {},
      filterTab: null,
    }
  },
  methods: {
    getDateRange: function (num, resolution) {
      let now = dayjs.utc()
      let then = now.subtract(num, resolution)

      let chipType = 'datetime_range'
      let chipValue = then.format('YYYY-MM-DD') + ',' + now.format('YYYY-MM-DD')
      this.chip = {
        field: '',
        type: chipType,
        value: chipValue,
        operator: 'must',
        active: true,
      }
      this.$emit('addChip', this.chip)
      this.$emit('cancel')

return {'start': now, 'end': then}
    },
    submit: function() {
      // Single date
      if (this.singleDate) {
        let chipType = 'datetime_range'
        let chipValue = this.singleDate + ',' + this.singleDate
        this.chip = {
          field: '',
          type: chipType,
          value: chipValue,
          operator: 'must',
          active: true,
        }
        this.$emit('addChip', this.chip)
        this.singleDate = null
      }

      // Timerange
      if (Object.keys(this.timerange).length !== 0) {
        let startDateTime = this.timerange.startDate + 'T' + this.timerange.startTime
        let endDateTime = this.timerange.endDate + 'T' + this.timerange.endTime
        let chipType = 'datetime_range'
        let chipValue = startDateTime+ ',' + endDateTime
        this.chip = {
          field: '',
          type: chipType,
          value: chipValue,
          operator: 'must',
          active: true,
        }
        this.$emit('addChip', this.chip)
        this.timerange = {}
      }
      this.$emit('cancel')
    }
  }
}
</script>

<style scoped lang="scss"></style>
