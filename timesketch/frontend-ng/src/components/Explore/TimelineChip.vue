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
  <v-menu offset-y content-class="menu-with-gap">
    <template v-slot:activator="{ on }">
      <v-chip v-on="on" :style="getTimelineStyle(timeline)">
        {{ timeline.name }}
        <v-avatar right style="background-color: rgba(0, 0, 0, 0.1); font-size: 0.55em">
          {{ eventsCount | compactNumber }}
        </v-avatar>
      </v-chip>
    </template>
    <v-card width="300">
      <v-list>
        <v-list-item v-if="timelineStatus === 'ready'">
          <v-list-item-action>
            <v-icon>mdi-square-edit-outline</v-icon>
          </v-list-item-action>
          <v-list-item-subtitle>Rename timeline</v-list-item-subtitle>
        </v-list-item>

        <v-list-item @click="$emit('toggle', timeline)" v-if="timelineStatus === 'ready'">
          <v-list-item-action>
            <v-icon v-if="isSelected">mdi-eye-off</v-icon>
            <v-icon v-else>mdi-eye</v-icon>
          </v-list-item-action>
          <v-list-item-subtitle v-if="isSelected">Temporarily disabled</v-list-item-subtitle>
          <v-list-item-subtitle v-else>Re-enable</v-list-item-subtitle>
        </v-list-item>
        <v-dialog v-model="dialogStatus" width="600">
          <template v-slot:activator="{ on, attrs }">
            <v-list-item v-bind="attrs" v-on="on">
              <v-list-item-action>
                <v-icon>{{ iconStatus }}</v-icon>
              </v-list-item-action>
              <v-list-item-subtitle>Status</v-list-item-subtitle>
            </v-list-item>
          </template>
          <v-card>
            <v-app-bar flat dense>Detailed information for: {{ timeline.name }}</v-app-bar>
            <v-card-text class="pa-5">
              <ul style="list-style-type: none">
                <li><strong>Opensearch index: </strong>{{ timeline.searchindex.index_name }}</li>
                <li v-if="timelineStatus === 'processing' || timelineStatus === 'ready'">
                  <strong>Number of events: </strong>
                  {{ allIndexedEvents | compactNumber }}
                </li>
                <li><strong>Created by: </strong>{{ timeline.user.username }}</li>
                <li>
                  <strong>Created at: </strong>{{ timeline.created_at | shortDateTime }}
                  <small>({{ timeline.created_at | timeSince }})</small>
                </li>
                <li v-if="timelineStatus === 'processing'">
                  <strong>Percentage Completed</strong> {{ Math.floor(percentage) }} %
                </li>
                <li v-if="timelineStatus === 'processing'">
                  <strong>Remaining time:</strong> {{ secondsToString(deltaRT) }}
                </li>
              </ul>
              <br /><br />
              <v-alert
                v-for="datasource in datasources"
                :key="datasource.id"
                colored-border
                border="left"
                elevation="1"
                :type="datasourceStatusColors(datasource)"
              >
                <ul style="list-style-type: none">
                  <li>
                    <strong>Total File Events:</strong
                    >{{ totalEventsDatasource(datasource.file_on_disk) | compactNumber }}
                  </li>
                  <li v-if="datasource.status[0].status === 'fail'">
                    <strong>Error message:</strong>
                    <code v-if="datasource.error_message"> {{ datasource.error_message }}</code>
                  </li>

                  <li><strong>Provider:</strong> {{ datasource.provider }}</li>
                  <li><strong>File on disk:</strong> {{ datasource.file_on_disk }}</li>
                  <li><strong>File size:</strong> {{ datasource.file_size | compactBytes }}</li>
                  <li><strong>Original filename:</strong> {{ datasource.original_filename }}</li>
                  <li><strong>Data label:</strong> {{ datasource.data_label }}</li>
                  <li><strong>Status:</strong> {{ datasource.status[0].status }}</li>
                </ul>
                <br />
              </v-alert>
              <v-progress-linear
                v-if="timelineStatus === 'processing'"
                color="light-blue"
                height="10"
                :value="Math.floor(percentage)"
                striped
              ></v-progress-linear>
            </v-card-text>
            <v-divider></v-divider>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn color="primary" text @click="dialogStatus = false"> Close </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-list>
    </v-card>
  </v-menu>
</template>

<script>
import Vue from 'vue'
import _ from 'lodash'

import EventBus from '../../main'
import TsTimelineStatusInformation from '../TimelineStatusInformation'
import ApiClient from '../../utils/RestApiClient'

export default {
  props: ['timeline', 'eventsCount', 'isSelected', 'isEmptyState'],
  components: {
    TsTimelineStatusInformation,
  },
  data() {
    return {
      initialColor: {},
      newColor: '',
      newTimelineName: '',
      colorPickerActive: false,
      showInfoModal: false,
      showEditModal: false,
      showAnalyzerModal: false,
      isDarkTheme: false,
      autoRefresh: false,
      allIndexedEvents: 0, // all indexed events from ready and processed datasources
      totalEvents: null,
      dialogStatus: false,
      datasources: [],
      deltaIndexedEvents: [],
    }
  },
  computed: {
    meta() {
      return this.$store.state.meta
    },
    datasourceErrors() {
      return this.timeline.datasources.filter((datasource) => datasource.error_message)
    },
    sketch() {
      return this.$store.state.sketch
    },

    timelineStatus() {
      let datasources_status = this.datasources.map((x) => x.status[0].status)
      if (datasources_status.every((status) => status === 'fail')) {
        return 'fail'
      }
      if (datasources_status.some((status) => status === 'processing' || status === null)) {
        return 'processing'
      }
      return 'ready'
    },
    IER() {
      // IER = Indexed Events Rate
      return this.deltaIndexedEvents.reduce((a, b) => a + b, 0) / Math.max(this.deltaIndexedEvents.length * 5, 1)
    },
    APE() {
      // APE = All Processing Events
      return this.datasources
        .filter((x) => x.status[0].status === 'processing')
        .map((x) => x.total_file_events)
        .reduce((a, b) => a + b, 0)
    },
    t0() {
      let listCreationDatasource = this.datasources
        .filter((x) => x.status[0].status === 'processing')
        .map((x) => {
          let t = new Date(x.created_at)
          return t.getTime() / 1000
        })
      return Math.min(...listCreationDatasource)
    },
    deltaTotal() {
      // the total time to upload the processing datasource
      if (this.IER === 0) return 0
      return this.APE / this.IER
    },
    deltaRT() {
      // delta Remaining Time
      if (this.deltaTotal === 0) return 100000 // transitory situation
      let t = new Date()
      let tNow = t.getTime() / 1000
      return Math.max(this.deltaTotal - (tNow - this.t0), 0)
    },
    percentage() {
      if (this.IER === 0) return 0
      return (1 - this.deltaRT / this.deltaTotal) * 100
    },
    iconStatus() {
      if (this.timelineStatus === 'ready') return 'mdi-check-circle'
      if (this.timelineStatus === 'processing') return 'mdi-circle-slice-7'
      return 'mdi-alert-circle'
    },
  },
  methods: {
    showColorPicker() {
      this.$refs.colorPicker.click()
    },
    rename() {
      this.showEditModal = false
      this.$emit('save', this.timeline, this.newTimelineName)
    },
    remove() {
      if (confirm('Delete the timeline?')) {
        this.$emit('remove', this.timeline)
      }
    },
    // Set debounce to 300ms if full Chrome colorpicker is used.
    updateColor: _.debounce(function (color) {
      this.newColor = color.hex
      if (this.newColor.startsWith('#')) {
        this.newColor = this.newColor.substring(1)
      }
      Vue.set(this.timeline, 'color', this.newColor)
      this.$emit('save', this.timeline)
    }, 0),
    toggleTheme: function () {
      this.isDarkTheme = !this.isDarkTheme
    },
    getTimelineStyle(timeline) {
      let backgroundColor = timeline.color
      let textDecoration = 'none'
      let opacity = '50%'
      let p = 100
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
      }
      if (this.timelineStatus === 'ready') {
        // Grey out the index if it is not selected.
        if (!this.isSelected) {
          backgroundColor = '#d2d2d2'
          textDecoration = 'line-through'
        } else {
          opacity = '100%'
        }
      } else if (this.timelineStatus === 'processing') {
        p = this.percentage
      } else {
        backgroundColor = '#631c1c'
        textDecoration = 'line-through'
      }
      let bgColor = 'linear-gradient(90deg, ' + backgroundColor + ' ' + p + '%, #d2d2d2  0%) '
      if (this.$vuetify.theme.dark) {
        return {
          background: bgColor,
          filter: 'grayscale(25%)',
          color: '#333',
        }
      }
      return {
        background: bgColor,
        'text-decoration': textDecoration,
        opacity: opacity,
      }
    },
    fetchData() {
      ApiClient.getSketchTimeline(this.sketch.id, this.timeline.id)
        .then((response) => {
          this.datasources = response.data.objects[0].datasources
          let tmpAllIndexedEvents = this.allIndexedEvents
          this.allIndexedEvents = response.data.meta.lines_indexed
          let deltaEvents = this.allIndexedEvents - tmpAllIndexedEvents
          if (deltaEvents < 10000) {
            // clean data: deltaEvents greater than 10K is related to Server "errors"
            this.deltaIndexedEvents.push(deltaEvents) // difference of indexed events from one iteration to the other one
          }
          if (this.timelineStatus !== 'ready' && this.timelineStatus !== 'fail') {
            this.autoRefresh = true
          } else {
            this.autoRefresh = false
            this.$store.dispatch('updateSketch', this.sketch.id).then(() => {
              this.$emit('toggle', response.data.objects[0])
            })
          }
        })
        .catch((e) => {})
    },
    secondsToString(d) {
      d = Number(d)
      var h = Math.floor(d / 3600)
      var m = Math.floor((d % 3600) / 60)
      var s = Math.floor((d % 3600) % 60)

      var hDisplay = h > 0 ? h + (h === 1 ? ' hour, ' : ' hours, ') : ''
      var mDisplay = m > 0 ? m + (m === 1 ? ' minute, ' : ' minutes, ') : ''
      var sDisplay = s > 0 ? s + (s === 1 ? ' second' : ' seconds') : ''
      return hDisplay + mDisplay + sDisplay
    },
    datasourceStatusColors(datasource) {
      if (datasource.status[0].status === 'ready' || datasource.status === []) {
        return 'info'
      } else if (datasource.status[0].status === 'processing') {
        return 'warning'
      }
      // status = fail
      return 'error'
    },
    totalEventsDatasource(fileOnDisk) {
      return this.datasources.find((x) => x.file_on_disk === fileOnDisk).total_file_events
    },
  },
  mounted() {
    // Hide color picker when clicked outside.
    let self = this // it might look redundant, but removing it breaks things
    window.addEventListener('click', function (e) {
      if (!self.$el.contains(e.target)) {
        self.colorPickerActive = false
      }
    })
  },
  created() {
    this.isDarkTheme = localStorage.theme === 'dark'
    EventBus.$on('isDarkTheme', this.toggleTheme)

    this.initialColor = {
      hex: this.timeline.color,
    }
    this.datasources = this.timeline.datasources
    if (this.timelineStatus === 'processing') {
      this.autoRefresh = true
      this.fetchData()
    } else {
      this.deltaIndexedEvents = []
      this.autoRefresh = false
      this.allIndexedEvents = this.meta.stats_per_timeline[this.timeline.id]['count']
    }
    this.newTimelineName = this.timeline.name
  },
  beforeDestroy() {
    clearInterval(this.t)
    this.t = false
  },
  watch: {
    autoRefresh(val) {
      if (val && !this.t) {
        this.t = setInterval(
          function () {
            this.fetchData()
          }.bind(this),
          5000
        )
      } else {
        clearInterval(this.t)
        this.t = false
        this.deltaIndexedEvents = []
      }
    },
    timeline() {
      if (this.timeline.datasources.length > this.datasources.length) {
        this.fetchData()
      } else {
        this.deltaIndexedEvents = []
      }
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
