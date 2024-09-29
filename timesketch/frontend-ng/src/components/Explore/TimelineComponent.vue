<!--
Copyright 2023 Google Inc. All rights reserved.

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
<!--
  A generic timeline component that provides common timeline related
  functionality and allows customization of the template. That way a timeline
  can be represented as a chip or a table row.
-->
<template>
  <span>
    <v-dialog v-if="timelineStatus === 'processing'" v-model="dialogStatus" width="600">
      <template v-slot:activator="{ on, attrs }">
        <slot
          name="processing"
          :timelineStatus="timelineStatus"
          :events="{
            on,
          }"
        > </slot>
      </template>
      <v-card>
        <v-app-bar flat dense>Importing events to timeline "{{ timeline.name }}"</v-app-bar>
        <div class="pa-5">
          <ul>
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
          </ul>
          <br />

          <div class="mb-3">{{ datasourcesProcessing.length }} datasource(s) in progress..</div>
          <v-alert
            v-for="datasource in datasourcesProcessing"
            :key="datasource.id"
            colored-border
            border="left"
            elevation="1"
            :color="datasourceStatusColors(datasource)"
          >
            <ul>
              <li><strong>Original filename:</strong> {{ datasource.original_filename }}</li>
              <li><strong>File on disk:</strong> {{ datasource.file_on_disk }}</li>
              <li><strong>File size:</strong> {{ datasource.file_size | compactBytes }}</li>
              <li><strong>Uploaded by:</strong> {{ datasource.user.username }}</li>
              <li><strong>Provider:</strong> {{ datasource.provider }}</li>
              <li><strong>Context:</strong> {{ datasource.context }}</li>
              <li v-if="datasource.data_label"><strong>Data label:</strong> {{ datasource.data_label }}</li>
              <li><strong>Status:</strong> {{ dataSourceStatus(datasource) }}</li>
              <li>
                <strong>Total File Events:</strong>{{ totalEventsDatasource(datasource.file_on_disk) | compactNumber }}
              </li>
              <li v-if="dataSourceStatus(datasource) === 'fail'">
                <strong>Error message:</strong>
                <code v-if="datasource.error_message"> {{ datasource.error_message }}</code>
              </li>
            </ul>
            <br />
          </v-alert>

          <v-card outlined v-if="percentComplete > 0.1">
            <v-card-title>{{ eventsPerSecond.slice(-1)[0] }} events/s</v-card-title>
            <v-sparkline
              :value="eventsPerSecond"
              :gradient="sparkline.gradient"
              :smooth="sparkline.radius || false"
              :padding="sparkline.padding"
              :line-width="sparkline.width"
              :stroke-linecap="sparkline.lineCap"
              :gradient-direction="sparkline.gradientDirection"
              :fill="sparkline.fill"
              :type="sparkline.type"
              :auto-line-width="sparkline.autoLineWidth"
              auto-draw
            >
            </v-sparkline>
            <v-sheet class="py-4 px-3">
              <v-progress-linear color="light-blue" height="25" :value="percentComplete" rounded>
                {{ percentComplete }}% (complete {{ processingETA() }})
              </v-progress-linear>
            </v-sheet>
          </v-card>
          <v-card v-else outlined class="pa-3"> Waiting for processing to begin.. </v-card>
        </div>
        <v-divider></v-divider>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="dialogStatus = false"> Close </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-menu
      v-else
      offset-y
      max-width="385"
      :close-on-content-click="false"
      content-class="menu-with-gap"
      ref="timelineChipMenuRef"
    >
      <template v-slot:activator="{ on }">
        <slot
          name="processed"
          :timelineFailed="timelineFailed"
          :timelineChipColor="timelineChipColor"
          :timelineStatus="timelineStatus"
          :events="{
            toggleTimeline,
            openDialog,
            menuOn: on,
          }"
        ></slot>
      </template>
      <v-sheet flat>
        <v-list dense>
          <v-dialog v-model="dialogRename" width="600">
            <template v-slot:activator="{ on, attrs }">
              <v-list-item v-bind="attrs" v-on="on">
                <v-list-item-action>
                  <v-icon>mdi-square-edit-outline</v-icon>
                </v-list-item-action>
                <v-list-item-subtitle>Rename</v-list-item-subtitle>
              </v-list-item>
            </template>
            <v-card class="pa-4">
              <v-form @submit.prevent="rename()">
                <h3>Rename timeline</h3>
                <br />
                <v-text-field clearable outlined dense autofocus v-model="newTimelineName" @focus="$event.target.select()" :rules="timelineNameRules">
                </v-text-field>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn text @click="dialogRename = false"> Cancel </v-btn>
                  <v-btn :disabled="!newTimelineName || newTimelineName.length > 255" color="primary" text @click="rename()"> Save </v-btn>
                </v-card-actions>
              </v-form>
            </v-card>
          </v-dialog>

          <v-list-item v-if="timelineStatus === 'ready'" @click="$emit('toggle', timeline)">
            <v-list-item-action>
              <v-icon v-if="isSelected">mdi-eye-off</v-icon>
              <v-icon v-else>mdi-eye</v-icon>
            </v-list-item-action>
            <v-list-item-subtitle v-if="isSelected">Temporarily disabled</v-list-item-subtitle>
            <v-list-item-subtitle v-else>Re-enable</v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="timelineStatus === 'ready'" @click="$emit('disableAllOtherTimelines', timeline)">
            <v-list-item-action>
              <v-icon>mdi-checkbox-marked-circle-minus-outline</v-icon>
            </v-list-item-action>
            <v-list-item-subtitle>Unselect other timelines</v-list-item-subtitle>
          </v-list-item>

          <v-dialog v-model="dialogStatus" width="800">
            <template v-slot:activator="{ on, attrs }">
              <v-list-item v-bind="attrs" v-on="on">
                <v-list-item-action>
                  <v-icon :color="iconStatus === 'mdi-alert-circle-outline' ? 'red' : ''">{{ iconStatus }}</v-icon>
                </v-list-item-action>
                <v-list-item-subtitle>Data sources ({{ datasources.length }})</v-list-item-subtitle>
              </v-list-item>
            </template>
            <v-card>
              <div class="pa-4">
                <ul style="list-style-type: none">
                  <li><strong>Timeline name: </strong>{{ timeline.name }}</li>
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
                  <li><strong>Number of datasources: </strong>{{ datasources.length }}</li>
                </ul>

                <v-alert
                  v-for="datasource in datasources"
                  :key="datasource.id"
                  outlined
                  text
                  :color="datasourceStatusColors(datasource)"
                  class="ma-5"
                >
                  <ul style="list-style-type: none">
                    <li><strong>Original filename:</strong> {{ datasource.original_filename }}</li>
                    <li><strong>File on disk:</strong> {{ datasource.file_on_disk }}</li>
                    <li><strong>File size:</strong> {{ datasource.file_size | compactBytes }}</li>
                    <li><strong>Uploaded by:</strong> {{ datasource.user.username }}</li>
                    <li><strong>Provider:</strong> {{ datasource.provider }}</li>
                    <li><strong>Context:</strong> {{ datasource.context }}</li>
                    <li v-if="datasource.data_label"><strong>Data label:</strong> {{ datasource.data_label }}</li>
                    <li><strong>Status:</strong> {{ dataSourceStatus(datasource) }}</li>
                    <li>
                      <strong>Total File Events: </strong
                      >{{ totalEventsDatasource(datasource.file_on_disk) | compactNumber }}
                    </li>
                    <li v-if="dataSourceStatus(datasource) === 'fail'">
                      <strong>Error message:</strong>
                      <code v-if="datasource.error_message"> {{ datasource.error_message }}</code>
                    </li>
                  </ul>
                </v-alert>
              </div>
              <v-divider></v-divider>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary" text @click="dialogStatus = false"> Close </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>

          <v-list-item
            v-if="timelineStatus === 'ready'"
            :to="{ name: 'Analyze', params: { sketchId: sketch.id, analyzerTimelineId: timeline.id } }"
            style="cursor: pointer"
            @click="$refs.timelineChipMenuRef.isActive = false"
          >
            <v-list-item-action>
              <v-icon>mdi-auto-fix</v-icon>
            </v-list-item-action>
            <v-list-item-subtitle>Run Analyzers</v-list-item-subtitle>
          </v-list-item>

          <v-list-item style="cursor: pointer" @click="deleteConfirmation = true">
            <v-list-item-action>
              <v-icon>mdi-trash-can-outline</v-icon>
            </v-list-item-action>
            <v-list-item-subtitle>Delete</v-list-item-subtitle>
          </v-list-item>
          <v-dialog v-model="deleteConfirmation" max-width="500">
            <v-card>
              <v-card-title>
                <v-icon color="red" class="mr-2 ml-n3">mdi-alert-octagon-outline</v-icon> Delete Timeline?
              </v-card-title>
              <v-card-text>
                <ul style="list-style-type: none">
                  <li><strong>Name: </strong>{{ timeline.name }}</li>
                  <li><strong>Status: </strong>{{ timelineStatus }}</li>
                  <li><strong>Opensearch index: </strong>{{ timeline.searchindex.index_name }}</li>
                  <li v-if="timelineStatus === 'processing' || timelineStatus === 'ready'">
                    <strong>Number of events: </strong>
                    {{ allIndexedEvents | compactNumber }}
                  </li>
                  <strong>Number of events: </strong>
                  {{
                    allIndexedEvents | compactNumber
                  }}
                  <li><strong>Created by: </strong>{{ timeline.user.username }}</li>
                  <li>
                    <strong>Created at: </strong>{{ timeline.created_at | shortDateTime }}
                    <small>({{ timeline.created_at | timeSince }})</small>
                  </li>
                </ul>
              </v-card-text>
              <v-card-actions>
                <v-btn color="primary" text @click="deleteConfirmation = false"> cancel </v-btn>
                <v-spacer></v-spacer>
                <v-btn color="primary" text @click="remove()"> delete </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-list>
        <div v-if="!timelineFailed" class="px-4">
          <v-color-picker
            @update:color="updateColor"
            :value="timeline.color"
            :show-swatches="!showCustomColorPicker"
            :swatches="colorPickerSwatches"
            :hide-canvas="!showCustomColorPicker"
            :hide-sliders="!showCustomColorPicker"
            hide-inputs
            mode="hexa"
            dot-size="15"
          ></v-color-picker>
          <v-btn text x-small class="mt-2" @click="showCustomColorPicker = !showCustomColorPicker">
            <span v-if="showCustomColorPicker">Palette</span>
            <span v-else>Custom color</span>
          </v-btn>
        </div>
        <br />
      </v-sheet>
    </v-menu>
  </span>
</template>

<script>
import Vue from 'vue'
import _ from 'lodash'
import dayjs from '@/plugins/dayjs'
import ApiClient from '../../utils/RestApiClient'

const gradients = [
  ['#222'],
  ['#42b3f4'],
  ['red', 'orange', 'yellow'],
  ['purple', 'violet'],
  ['#00c6ff', '#F0F', '#FF0'],
  ['#f72047', '#ffd200', '#1feaea'],
]

export default {
  props: ['timeline', 'eventsCount', 'isSelected', 'isEmptyState'],
  data() {
    return {
      autoRefresh: false,
      allIndexedEvents: 0, // all indexed events from ready and processed datasources
      totalEvents: null,
      dialogStatus: false,
      dialogRename: false,
      datasources: [],
      timelineStatus: null,
      eventsPerSecond: [],
      newTimelineName: [...this.timeline.name],
      sparkline: {
        width: 2,
        radius: 10,
        padding: 8,
        lineCap: 'round',
        gradient: gradients[5],
        gradientDirection: 'bottom',
        gradients,
        fill: false,
        type: 'trend',
        autoDrawDuration: 4000,
        autoLineWidth: false,
      },
      showCustomColorPicker: false,
      colorPickerSwatches: [
        ['#5E75C2', '#BB77C4', '#FD7EAC'],
        ['#FF9987', '#FFC66A', '#F9F871'],
        ['#FFB5BC', '#97D788', '#9BC1AF'],
        ['#FFC7A0', '#FFDF79', '#FFEAEF'],
        ['#DEBBFF', '#9AB0FB', '#CFFBE2'],
      ],
      deleteConfirmation: false,
      timelineNameRules: [
        (v) => !!v || 'Timeline name is required.',
        (v) => (v && v.length <= 255) || 'Timeline name is too long.',
      ],
    }
  },
  computed: {
    meta() {
      return this.$store.state.meta
    },
    datasourceErrors() {
      return this.timeline.datasources.filter((datasource) => datasource.error_message)
    },
    datasourcesProcessing() {
      return this.datasources.filter(
        (datasource) =>
          this.dataSourceStatus(datasource) === 'processing' || this.dataSourceStatus(datasource) === 'queueing'
      )
    },
    sketch() {
      return this.$store.state.sketch
    },
    totalEventsToIndex() {
      return this.datasources
        .filter((x) => this.dataSourceStatus(x) === 'processing')
        .map((x) => x.total_file_events)
        .reduce((a, b) => a + b, 0)
    },
    secondsToComplete() {
      return this.totalEventsToIndex / this.avarageEventsPerSecond()
    },
    percentComplete() {
      return Math.floor((this.secondsSinceStart() / this.secondsToComplete) * 100) || 0
    },
    iconStatus() {
      if (this.timelineStatus === 'ready') return 'mdi-information-outline'
      if (this.timelineStatus === 'processing') return 'mdi-circle-slice-7'
      return 'mdi-alert-circle-outline'
    },
    timelineFailed() {
      return this.timelineStatus === 'fail'
    },
    timelineChipColor() {
      if (!this.timeline.color.startsWith('#')) {
        return '#' + this.timeline.color
      }
      return this.timeline.color
    },
  },
  methods: {
    openDialog() {
      this.dialogStatus = true
    },
    rename() {
      this.dialogRename = false
      this.$emit('save', this.timeline, this.newTimelineName)
    },
    remove() {
      this.$emit('remove', this.timeline)
      this.deleteConfirmation = false
      this.successSnackBar('Timeline deleted')
    },
    secondsSinceStart() {
      if (!this.datasourcesProcessing.length) {
        return 0
      }
      let start = dayjs.utc(this.datasourcesProcessing[0].updated_at)
      let end = dayjs.utc()
      let diffSeconds = end.diff(start, 'second')
      return diffSeconds
    },
    avarageEventsPerSecond() {
      const sum = this.eventsPerSecond.reduce((a, b) => a + b, 0)
      const avg = sum / this.eventsPerSecond.length || 0
      return Math.floor(avg)
    },
    processingETA() {
      let secondsLeft = this.secondsToComplete - this.secondsSinceStart()
      let eta = dayjs.utc().add(secondsLeft, 'second').fromNow()
      return eta
    },
    toggleTimeline() {
      if (!this.timelineFailed) {
        this.$emit('toggle', this.timeline)
      }
    },
    // Set debounce to 300ms to limit requests to the server.
    updateColor: _.debounce(function (color) {
      Vue.set(this.timeline, 'color', color.hex.substring(1))
      this.$emit('save', this.timeline)
    }, 300),
    fetchData() {
      ApiClient.getSketchTimeline(this.sketch.id, this.timeline.id)
        .then((response) => {
          this.timelineStatus = response.data.objects[0].status[0].status
          this.datasources = response.data.objects[0].datasources
          // This is a naive approach and is misleading if there are multiple
          // datasources importing at the same time, or multiple timelines importing to
          // the same index.
          //
          // TODO: Add datasource ID to all events at import time like we do with
          // timeline ID. This will give us the ability to calculate index progress per
          // datasource, and also enable deletion of datasources from opensearch
          // indices.
          //
          // Tracking in: https://github.com/google/timesketch/issues/2361
          let tmpAllIndexedEvents = this.allIndexedEvents
          this.allIndexedEvents = response.data.meta.lines_indexed
          let deltaEvents = this.allIndexedEvents - tmpAllIndexedEvents

          if (deltaEvents < 10000 && deltaEvents > 0) {
            this.eventsPerSecond.push(Math.floor(deltaEvents / 5))
          }

          if (this.timelineStatus !== 'ready' && this.timelineStatus !== 'fail') {
            this.autoRefresh = true
          } else {
            this.autoRefresh = false
            this.$store.dispatch('updateSketch', this.sketch.id).then(() => {
              if (this.timelineStatus === 'ready') this.$emit('toggle', response.data.objects[0])
            })
          }
        })
        .catch((e) => {
          console.log(e)
        })
    },
    dataSourceStatus(datasource) {
      // Support legacy datasources that don't have a status set.
      if (!datasource.status[0]) {
        return 'ready'
      }

      return datasource.status[0].status
    },

    datasourceStatusColors(datasource) {
      // Support legacy datasources that don't have a status set.
      if (!datasource.status[0]) {
        return 'ready'
      }

      if (datasource.status[0].status === 'ready' || datasource.status === []) {
        return 'success'
      } else if (datasource.status[0].status === 'processing') {
        return 'info'
      } else if (datasource.status[0].status === 'queueing') {
        return 'warning'
      }
      // status = fail
      return 'error'
    },
    totalEventsDatasource(fileOnDisk) {
      return this.datasources.find((x) => x.file_on_disk === fileOnDisk).total_file_events
    },
  },
  created() {
    // TODO: Move to computed
    this.timelineStatus = this.timeline.status[0].status

    this.datasources = this.timeline.datasources
    let timelineStat = this.meta.stats_per_timeline[this.timeline.id]

    if (this.timelineStatus === 'processing') {
      this.autoRefresh = true
    } else {
      this.autoRefresh = false
      if (timelineStat) {
        this.allIndexedEvents = timelineStat['count']
      }
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
      }
    },
    timeline() {
      if (this.timeline.datasources.length > this.datasources.length) {
        this.fetchData()
      }
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.timeline-chip {
  .right {
    margin-left: auto;
  }

  .chip-content {
    margin: 0;
    padding: 0;
    display: flex;
    align-items: center;
    width: 300px;
  }
}

.v-chip.timeline-chip.failed {
  cursor: auto;
}

.v-chip.timeline-chip.failed:hover:before {
  opacity: 0;
}

.events-count {
  font-size: 0.8em;
}

.disabled {
  text-decoration: line-through;
}
</style>
