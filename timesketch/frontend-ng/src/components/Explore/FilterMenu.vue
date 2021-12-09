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
          <v-row>
            <v-col cols="8">
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

          <v-row dense>
            <v-col cols="8">
              <v-menu transition="scale-transition" offset-y min-width="auto">
                <template v-slot:activator="{ on, attrs }">
                  <v-text-field v-model="startDate" label="Start date" v-bind="attrs" v-on="on">{{
                    startDate
                  }}</v-text-field>
                </template>
                <v-date-picker v-model="startDate" no-title> </v-date-picker>
              </v-menu>
            </v-col>

            <v-col cols="4">
              <v-menu transition="scale-transition" offset-y min-width="auto" :close-on-content-click="false">
                <template v-slot:activator="{ on, attrs }">
                  <v-text-field v-model="startTime" label="hh:mm:ss" v-bind="attrs" v-on="on">{{
                    startTime
                  }}</v-text-field>
                </template>

                <v-time-picker v-model="startTime" format="24hr" use-seconds> </v-time-picker>
              </v-menu>
            </v-col>
          </v-row>

          <v-row dense>
            <v-col cols="8">
              <v-menu transition="scale-transition" offset-y min-width="auto">
                <template v-slot:activator="{ on, attrs }">
                  <v-text-field v-model="endDate" label="End date" v-bind="attrs" v-on="on">{{ endDate }}</v-text-field>
                </template>

                <v-date-picker v-model="endDate" no-title> </v-date-picker>
              </v-menu>
            </v-col>
            <v-col cols="4">
              <v-menu transition="scale-transition" offset-y min-width="auto" :close-on-content-click="false">
                <template v-slot:activator="{ on, attrs }">
                  <v-text-field v-model="endTime" label="hh:mm:ss" v-bind="attrs" v-on="on">{{ endTime }}</v-text-field>
                </template>
                <v-time-picker v-model="endTime" format="24hr" use-seconds> </v-time-picker>
              </v-menu>
            </v-col>
          </v-row>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn text color="primary" @click="$emit('cancel')"> Cancel </v-btn>
            <v-btn text color="primary" @click="$refs.menu.save(date)"> Add filter </v-btn>
          </v-card-actions>
        </v-container>
      </v-tab-item>
      <v-tab-item :transition="false">
        <v-container class="px-8">TBD</v-container>
      </v-tab-item>
    </v-tabs-items>
  </v-card>
</template>

<script>
export default {
  data() {
    return {
      filterTab: null,
    }
  },
}
</script>

<style scoped lang="scss"></style>
