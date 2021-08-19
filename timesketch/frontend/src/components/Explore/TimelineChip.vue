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
  <span>
    <span v-if="meta.permissions.write">
      <!-- Timeline info modal -->
      <b-modal :active.sync="showInfoModal" :width="1024" scroll="keep" style="z-index:999;">
        <div class="modal-background"></div>
        <div class="modal-content">
          <div class="card">
            <header class="card-header">
              <p class="card-header-title">Detailed information for {{ timeline.name }}</p>
            </header>
            <div class="card-content">
              <ul>
                <li>Elasticsearch index: {{ timeline.searchindex.index_name }}</li>
                <li v-if="meta.stats_per_timeline[timeline.id]">
                  Number of events: {{ meta.stats_per_timeline[timeline.id]['count'] | compactNumber }} ({{
                    meta.stats_per_timeline[timeline.id]['count']
                  }})
                </li>
                <li>Created by: {{ timeline.user.username }}</li>
                <li>Created at: {{ timeline.created_at | moment('YYYY-MM-DD HH:mm') }}</li>
              </ul>
              <br />

              <b-message
                v-for="datasource in timeline.datasources"
                :type="datasource.error_message ? 'is-danger' : 'is-success'"
                :title="datasource.created_at"
                :closable="false"
                :key="datasource.id"
              >
                <ul>
                  <li><strong>Provider:</strong> {{ datasource.provider }}</li>
                  <li><strong>Context:</strong> {{ datasource.context }}</li>
                  <li><strong>User:</strong> {{ datasource.user.username }}</li>
                  <li><strong>File on disk:</strong> {{ datasource.file_on_disk }}</li>
                  <li><strong>File size:</strong> {{ datasource.file_size | compactBytes }}</li>
                  <li><strong>Original filename:</strong> {{ datasource.original_filename }}</li>
                  <li><strong>Data label:</strong> {{ datasource.data_label }}</li>
                </ul>
                <br />
                <div v-if="datasource.error_message">
                  <strong style="font-size:1.2rem; margin-bottom:10px;">Error detail</strong>
                  <pre style="margin-top:10px;">{{ datasource.error_message }}</pre>
                </div>
              </b-message>
            </div>
          </div>
        </div>
        <button class="modal-close is-large" aria-label="close" @click="showInfoModal = !showInfoModal"></button>
      </b-modal>

      <!-- Timeline rename modal -->
      <b-modal :active.sync="showEditModal" :width="640" scroll="keep" style="z-index:999;">
        <div class="modal-background"></div>
        <div class="modal-content">
          <div class="card">
            <header class="card-header">
              <p class="card-header-title">Rename timeline</p>
            </header>
            <div class="card-content">
              <div class="content">
                <form @submit.prevent>
                  <!-- Without prevent(), the page will refresh -->
                  <div class="field">
                    <div class="control">
                      <input v-model="newTimelineName" class="input" type="text" required autofocus />
                    </div>
                  </div>
                  <div class="field">
                    <div class="control">
                      <input class="button is-success" @click="rename()" type="submit" value="Save" />
                    </div>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
        <button class="modal-close is-large" aria-label="close" @click="showEditModal = !showEditModal"></button>
      </b-modal>

      <!-- Analyzer logs modal -->
      <b-modal :active.sync="showAnalyzerModal" :width="1024" scroll="keep" style="z-index:999;">
        <div class="modal-background"></div>
        <div class="modal-content">
          <div class="card">
            <header class="card-header">
              <p class="card-header-title">Analyzer logs for {{ timeline.name }}</p>
            </header>
            <div class="card-content" v-if="showAnalyzerModal">
              <ts-analyzer-history :timeline="timeline" @closeHistory="showAnalyzerModal = false"></ts-analyzer-history>
            </div>
          </div>
        </div>
        <button
          class="modal-close is-large"
          aria-label="close"
          @click="showAnalyzerModal = !showAnalyzerModal"
        ></button>
      </b-modal>
    </span>

    <span
      class="tag is-medium has-text-left timeline-chip"
      :style="getTimelineStyle(timeline)"
      @click="toggleTimeline(timeline)"
    >
      {{ timeline.name }}
      <!-- Show a warning icon, if there were import errors. -->
      <span v-if="datasourceErrors.length" class="b-tooltips import-error" @click.stop>
        <b-tooltip :label="datasourceErrors.length + ' failed imports'" :type="isDarkTheme ? 'is-dark' : 'is-light'">
          <span class="icon is-small" style="color:orange;">
            <i class="fas fa-exclamation-triangle" @click="showInfoModal = !showInfoModal"></i>
          </span>
        </b-tooltip>
      </span>
      <span class="tag is-small timeline-count" style="color:#333;">
        <span v-if="isSelected && !isEmptyState">{{ eventsCount | compactNumber }} </span>
      </span>

      <span v-if="meta.permissions.write" @click.stop>
        <!-- 3-dots dropdown menu -->
        <ts-dropdown width="270px">
          <template v-slot:dropdown-trigger-element>
            <a role="button" style="color:#333;">
              <i class="fas fa-ellipsis-v" style="padding-left: 14px;padding-right: 6px;"></i>
            </a>
          </template>
          <div class="ts-dropdown-item" @click="showInfoModal = !showInfoModal">
            <span class="icon is-small"><i class="fas fa-info-circle"></i></span>
            <span>Info</span>
          </div>

          <div class="ts-dropdown-item" v-if="timelineStatus === 'ready'" @click="showEditModal = !showEditModal">
            <span class="icon is-small">
              <i class="fas fa-edit"></i>
            </span>
            <span>Rename</span>
          </div>

          <div
            class="ts-dropdown-item"
            v-if="timelineStatus === 'ready'"
            @click="showAnalyzerModal = !showAnalyzerModal"
          >
            <span class="icon is-small"> <i class="fas fa-history"></i> </span>
            <span>Analyzer logs</span>
          </div>

          <div class="ts-dropdown-item" @click="remove()">
            <span class="icon is-small is-danger">
              <i class="fas fa-trash"></i>
            </span>
            <span>Delete</span>
          </div>

          <hr />

          <div v-if="timelineStatus === 'ready'">
            <color-picker
              v-model="initialColor"
              @input="updateColor"
              style="box-shadow: none; background-color: transparent; padding:0;"
              :palette="[
                '#55efc4',
                '#81ecec',
                '#74b9ff',
                '#a29bfe',
                '#00b894',
                '#00cec9',
                '#0984e3',
                '#6c5ce7',
                '#ffeaa7',
                '#fab1a0',
                '#ff7675',
                '#fd79a8',
                '#fdcb6e',
                '#e17055',
                '#ff4d4d',
                '#fffa65',
                '#e84393',
                '#f6e58d',
                '#ffbe76',
                '#ff7979',
                '#badc58',
                '#dff9fb',
                '#f9ca24',
                '#f0932b',
                '#eb4d4b',
                '#6ab04c',
                '#c7ecee',
                '#7ed6df',
                '#e056fd',
                '#686de0',
                '#95afc0',
                '#22a6b3',
                '#4bcffa',
                '#34e7e4',
                '#0be881',
                '#ffdd59',
              ]"
            ></color-picker>
          </div>
        </ts-dropdown>
      </span>
    </span>
  </span>
</template>

<script>
import Vue from 'vue'
import { Compact } from 'vue-color'
import _ from 'lodash'

import TsAnalyzerHistory from '../Analyze/AnalyzerHistory'
import TsDropdown from '../Common/Dropdown'

import EventBus from '../../main'

export default {
  components: {
    'color-picker': Compact,
    TsAnalyzerHistory,
    TsDropdown,
  },
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
      return this.timeline.datasources.filter(datasource => datasource.error_message)
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
    updateColor: _.debounce(function(color) {
      this.newColor = color.hex
      if (this.newColor.startsWith('#')) {
        this.newColor = this.newColor.substring(1)
      }
      Vue.set(this.timeline, 'color', this.newColor)
      this.$emit('save', this.timeline)
    }, 0),
    toggleTheme: function() {
      this.isDarkTheme = !this.isDarkTheme
    },
    getTimelineStyle(timeline) {
      this.isDarkTheme = localStorage.theme === 'dark'
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

      if (this.isDarkTheme) {
        return {
          'background-color': backgroundColor,
          'text-decoration': textDecoration,
          opacity: opacity,
          filter: 'grayscale(25%)',
          color: '#333333',
        }
      }
      return {
        'background-color': backgroundColor,
        'text-decoration': textDecoration,
        opacity: opacity,
      }
    },
    toggleTimeline: function(timeline) {
      this.$emit('toggle', timeline)
    },
  },
  mounted() {
    // Hide color picker when clicked outside.
    let self = this // it might look redundant, but removing it breaks things
    window.addEventListener('click', function(e) {
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
<style scoped lang="scss">
.icon {
  padding-right: 8px;
}
.timeline-chip {
  cursor: pointer;
  margin-right: 7px;
  margin-bottom: 7px;
  padding-right: 6px;
}
.timeline-count {
  margin-left: 10px;
  margin-right: -7px;
  background-color: rgba(255, 255, 255, 0.5);
  min-width: 50px;
}
.import-error {
  padding-right: 6px;
  padding-left: 12px;
}
</style>

<!-- It was tricky to remove padding from the Color Picker's dropdown -->
<style lang="scss">
.color-picker-dropdown .dropdown-content {
  padding: 0px !important;
}
</style>
