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
        <v-list-item @click="removeChip(chip)">
          <v-list-item-action>
            <v-icon>mdi-delete</v-icon>
          </v-list-item-action>
          <v-list-item-subtitle>Remove from sketch</v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </v-card>
  </v-menu>
</template>

<script>
import Vue from 'vue'
import _ from 'lodash'

import EventBus from '../../main'

export default {
  props: ['timeline', 'eventsCount', 'isSelected', 'isEmptyState'],
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
    }
  },
  computed: {
    meta() {
      return this.$store.state.meta
    },
    datasourceErrors() {
      return this.timeline.datasources.filter((datasource) => datasource.error_message)
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
      let opacity = '100%'
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
      }
      // Grey out the index if it is not selected.
      if (!this.isSelected) {
        backgroundColor = '#d2d2d2'
        textDecoration = 'line-through'
        opacity = '50%'
      }
      if (this.$vuetify.theme.dark) {
        return {
          'background-color': backgroundColor,
          filter: 'grayscale(25%)',
          color: '#333',
        }
      }
      return {
        'background-color': backgroundColor,
        'text-decoration': textDecoration,
        opacity: opacity,
      }
    },
    toggleTimeline: function (timeline) {
      this.$emit('toggle', timeline)
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
    this.newTimelineName = this.timeline.name
  },
  beforeDestroy() {
    clearInterval(this.t)
    this.t = false
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
