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
        <v-list-item>
          <v-list-item-action>
            <v-icon>mdi-square-edit-outline</v-icon>
          </v-list-item-action>
          <v-list-item-subtitle>Rename timeline</v-list-item-subtitle>
        </v-list-item>

        <v-list-item @click="toggleTimeline(timeline)">
          <v-list-item-action>
            <v-icon v-if="isSelected">mdi-eye-off</v-icon>
            <v-icon v-else>mdi-eye</v-icon>
          </v-list-item-action>
          <v-list-item-subtitle v-if="isSelected">Temporarily disabled</v-list-item-subtitle>
          <v-list-item-subtitle v-else>Re-enable</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <v-list-item-action>
            <ts-timeline-status-information
              :timeline="timeline"
              :indexedEvents="indexedEvents"
              :totalEvents="totalEvents"
              :timelineStatus="timelineStatus"
            ></ts-timeline-status-information>
          </v-list-item-action>
          <v-list-item-subtitle>Status</v-list-item-subtitle>
        </v-list-item>
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
      timelineStatus: '',
      colorPickerActive: false,
      showInfoModal: false,
      showEditModal: false,
      showAnalyzerModal: false,
      isDarkTheme: false,
      timelineStatus: null,
      autoRefresh: false,
      indexedEvents: 0,
      totalEvents: null,
    }
  },
  computed: {
    meta() {
      return this.$store.state.meta
    },
    datasourceErrors() {
      return this.timeline.datasources.filter((datasource) => datasource.error_message)
    },
    meta() {
      return this.$store.state.meta
    },
    sketch() {
      return this.$store.state.sketch
    },
    percentageTimeline() {
      let totalEvents = 1
      if (this.totalEvents) {
        totalEvents = this.totalEvents.total
      }
      let percentage = Math.min(Math.floor((this.indexedEvents / totalEvents) * 100), 100)
      if (this.timelineStatus === 'ready') percentage = 100
      return percentage
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
      // background: 'linear-gradient(90deg, ' + backgroundColor + ' ' + p + '%, #d2d2d2 ' + q + '%);'
      let backgroundColor = timeline.color
      let textDecoration = 'none'
      let opacity = '100%'
      let p = 100
      let animation = ''
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
      }

      if (this.timelineStatus === 'ready') {
        p = 100
        // Grey out the index if it is not selected.
        if (!this.isSelected) {
          backgroundColor = '#d2d2d2'
          textDecoration = 'line-through'
          opacity = '50%'
        }
      } else if (this.timelineStatus === 'processing') {
        animation = 'blinker 1s linear infinite'
        p = this.percentageTimeline
        opacity = '50%'
      }
      let bgColor = 'linear-gradient(90deg, ' + backgroundColor + ' ' + p + '%, #d2d2d2  0%) '
      if (this.$vuetify.theme.dark) {
        return {
          background: bgColor,
          filter: 'grayscale(25%)',
          color: '#333',
          animation: animation,
        }
      }
      return {
        background: bgColor,
        'text-decoration': textDecoration,
        opacity: opacity,
        animation: animation,
      }
    },
    toggleTimeline: function (timeline) {
      this.$emit('toggle', timeline)
    },
    fetchData() {
      ApiClient.getSketchTimeline(this.sketch.id, this.timeline.id)
        .then((response) => {
          this.timelineStatus = response.data.objects[0].status[0].status
          this.indexedEvents = response.data.meta.lines_indexed
          this.totalEvents = JSON.parse(response.data.objects[0].total_events)
          if (this.timelineStatus !== 'ready' && this.timelineStatus !== 'fail') {
            this.autoRefresh = true
          } else {
            this.autoRefresh = false
          }
        })
        .catch((e) => {})
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
    this.timelineStatus = this.timeline.status[0].status
    if (this.timelineStatus !== 'ready' && this.timelineStatus !== 'fail') {
      this.autoRefresh = true
    } else {
      this.autoRefresh = false
      this.indexedEvents = this.meta.stats_per_timeline[this.timeline.id]['count']
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
            if (this.timelineStatus === 'ready' || this.timelineStatus === 'fail') {
              this.autoRefresh = false
            }
          }.bind(this),
          5000
        )
      } else {
        clearInterval(this.t)
        this.t = false
      }
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
