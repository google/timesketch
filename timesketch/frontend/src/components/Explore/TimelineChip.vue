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
  <div>
    <span v-if="meta.permissions.write">

      <!-- Timeline info modal -->
      <b-modal :active.sync="showInfoModal" :width="1024" scroll="keep">
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
        <button class="modal-close is-large" aria-label="close" v-on:click="showInfoModal = !showInfoModal"></button>
      </b-modal>

      <!-- Timeline rename modal -->
    <b-modal :active.sync="showEditModal" :width="640" scroll="keep">
      <div class="modal-background"></div>
      <div class="modal-content">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Rename timeline</p>
          </header>
          <div class="card-content">
            <div class="content">
              <form v-on:submit.prevent> <!-- Without prevent(), the page will refresh -->
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
      <button class="modal-close is-large" aria-label="close" v-on:click="showEditModal = !showEditModal"></button>
    </b-modal>

    <!-- Analyzer logs modal -->
      <b-modal :active.sync="showAnalysisHistory" :width="1024" scroll="keep">
        <div class="modal-background"></div>
        <div class="modal-content">
          <div class="card">
            <header class="card-header">
              <p class="card-header-title">Analyzer logs for {{ timeline.name }}</p>
            </header>
            <div class="card-content" v-if="showAnalysisHistory">
              <ts-analyzer-history :timeline="timeline" @closeHistory="showAnalysisHistory = false"></ts-analyzer-history>
            </div>
          </div>
        </div>
        <button class="modal-close is-large" aria-label="close" v-on:click="showAnalysisHistory = !showAnalysisHistory"></button>
      </b-modal>

    </span>

    <span
      class="tag is-medium has-text-left"
      style="cursor: pointer; margin-right: 7px;margin-bottom:7px;padding-right: 6px;"
      v-bind:style="timelineColor(timeline)"
      v-on:click="toggleTimeline(timeline)"
    >
      {{ timeline.name }}
      <span
        class="tag is-small"
        style="margin-left:10px;margin-right:-7px;background-color: rgba(255,255,255,0.5);min-width:50px;"
      >
        <span v-if="timelineIsEnabled(timeline) && countPerTimeline">{{
          getCount(timeline) | compactNumber
        }}
        </span>
      </span>
      <span v-if="meta.permissions.write" v-on:click.stop>
        <b-dropdown append-to-body>
          <template #trigger>
            <a role="button">
              <i class="fas fa-ellipsis-v" style="padding-left: 14px;padding-right: 6px;"></i>
            </a>
          </template>
          <b-dropdown-item aria-role="listitem" v-on:click="showInfoModal = !showInfoModal">
            <span class="icon is-small"><i class="fas fa-info-circle"></i></span>
            <span>Info</span>
          </b-dropdown-item>
          <b-dropdown-item aria-role="listitem" v-if="timelineStatus === 'ready'" v-on:click="showEditModal = !showEditModal">
            <span class="icon is-small">
            <i class="fas fa-edit"></i>
            </span>
            <span>Rename</span>
          </b-dropdown-item>
          <b-dropdown-item aria-role="listitem" v-if="timelineStatus === 'ready'" v-on:click="showAnalysisHistory = !showAnalysisHistory">
            <span class="icon is-small">
            <i class="fas fa-history"></i>
            </span>
            <span>Analyzer logs</span>
          </b-dropdown-item>
          <b-dropdown-item aria-role="listitem" v-on:click="remove()" class="is-danger">
            <span class="icon is-small">
            <i class="fas fa-trash"></i>
            </span>
            <span>Delete</span>
          </b-dropdown-item>
        </b-dropdown>
      </span>
    </span>
  </div>
  <!-- <div class="tag is-medium has-text-left" style="background-color: #f5f5f5; padding-left: 5px;">
    <div
      style="width: 20px; height: 20px; border-radius: 6px; margin-right: 10px;"
      v-bind:style="timelineColorStyle"
    ></div>
    <div style="font-weight: normal;">{{ timeline.name }}</div>
  </div> -->
</template>

<script>
import Vue from 'vue'
import { Chrome } from 'vue-color'
import _ from 'lodash'

import ApiClient from '../../utils/RestApiClient'

import TsAnalyzerHistory from '../Analyze/AnalyzerHistory'

import EventBus from '../../main'

export default {
  components: {
    'color-picker': Chrome,
    TsAnalyzerHistory,
  },
  props: ['timeline', 'selectedTimelines', 'countPerIndex', 'countPerTimeline'],
  data() {
    return {
      initialColor: {},
      newColor: '',
      newTimelineName: '',
      colorPickerActive: false,
      showInfoModal: false,
      showEditModal: false,
      analysisSessionId: false,
      showAnalysisHistory: false,
      timelineStatus: null,
      autoRefresh: false,
      isOpen: false,
      isDarkTheme: false,
    }
  },
  computed: {
    meta() {
      return this.$store.state.meta
    },
    timelineColorStyle() {
      // TODO(bartoszi): Confirm if the below code is required
      //
      // let backgroundColor = this.newColor || this.timeline.color
      // if (!backgroundColor.startsWith('#')) {
      //   backgroundColor = '#' + backgroundColor
      // }
      // if (this.isDarkTheme) {
      //   return {
      //     'background-color': backgroundColor,
      //     filter: 'grayscale(25%)',
      //     color: '#333',
      //   }
      // }
      // return {
      //   'background-color': backgroundColor,
      // }

      let backgroundColor = this.timeline.color
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
      }
      return {
        'background-color': backgroundColor,
      }
    },
    datasourceErrors() {
      return this.timeline.datasources.filter(datasource => datasource.error_message)
    },
  },
  methods: {
    rename() {
      this.showEditModal = false
      this.$emit('save', this.timeline, this.newTimelineName)
    },
    remove() {
      if (confirm('Delete the timeline?')) {
        this.$emit('remove', this.timeline)
      }
    },
    updateColor: _.debounce(function(color) {
      this.newColor = color.hex
      if (this.newColor.startsWith('#')) {
        this.newColor = this.newColor.substring(1)
      }
      Vue.set(this.timeline, 'color', this.newColor)
      this.$emit('save', this.timeline)
    }, 300),
    fetchData() {
      ApiClient.getSketchTimeline(this.sketch.id, this.timeline.id)
        .then(response => {
          this.timelineStatus = response.data.objects[0].status[0].status
          if (this.timelineStatus !== 'ready') {
            this.autoRefresh = true
          }
          this.$store.dispatch('updateSketch', this.$store.state.sketch.id)
        })
        .catch(e => {})
    },
    openFilteredTimeline: function(index, dataTypes) {
      if (dataTypes.length === 0) {
        return false
      }
      let searchQuery = ''
      for (let i = 0; i < dataTypes.length; i++) {
        const dt = dataTypes[i]
        if (i !== 0) {
          searchQuery += ' OR '
        }
        searchQuery += 'data_type:"' + dt + '"'
      }
      this.$router.push({ name: 'Explore', query: { index: index, q: searchQuery } })
    },
    toggleTheme: function() {
      this.isDarkTheme = !this.isDarkTheme
    },
    timelineColor(timeline) {
      this.isDarkTheme = localStorage.theme === 'dark'
      let backgroundColor = timeline.color
      let textDecoration = 'none'
      let opacity = '100%'
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
      }
      // Grey out the index if it is not selected.
      if (!this.selectedTimelines.includes(timeline)) {
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
    timelineIsEnabled: function(timeline) {
      return this.selectedTimelines.includes(timeline)
    },
    getCount: function(timeline) {
      let count = this.countPerTimeline[timeline.id]
      // Support for old style indices
      if (count === undefined) {
        count = this.countPerIndex[timeline.searchindex.index_name]
      }
      return count
    },
  },
  mounted() {
    // Hide color picket when clicked outside.
    let self = this
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
    if (this.timelineStatus !== 'ready') {
      this.autoRefresh = true
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
          function() {
            this.fetchData()
            if (this.timelineStatus === 'ready') {
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
<style scoped lang="scss">
.list-item {
  display: inline-block;
  margin-right: 10px;
}
.list-enter-active,
.list-leave-active {
  transition: all 0.5s;
}
.list-enter,
.list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
.vc-sketch {
  box-shadow: none;
}
.blink {
  animation: blinker 1s linear infinite;
}
.checkbox-margin {
  margin-left: 10px;
  margin-right: 6px;
}
.small-top-margin {
  margin-top: 4px;
}

@keyframes blinker {
  50% {
    opacity: 40%;
  }
}

.table th {
  color: var(--default-font-color);
}
</style>
