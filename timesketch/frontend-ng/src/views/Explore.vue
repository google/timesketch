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
  <v-container fluid>
    <!-- Right side menu for selected events -->
    <v-navigation-drawer
      v-model="selectedEvents.length"
      fixed
      right
      width="600"
      style="box-shadow: 0 10px 15px -3px #888"
    >
      <template v-slot:prepend>
        <v-toolbar flat>
          <v-toolbar-title>{{ selectedEvents.length }} events selected</v-toolbar-title>

          <v-spacer></v-spacer>

          <v-btn icon @click="selectedEvents = []">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
      </template>

      <v-container>
        <v-list>
          <v-list-item v-for="(event, index) in selectedEvents" :key="index">
            <v-list-item-content>
              <v-list-item-title>{{ event._source.message }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-container>
    </v-navigation-drawer>

    <!-- Scenarios left panel -->
    <v-navigation-drawer
      v-if="scenario.facets.length"
      app
      permanent
      :width="rightSidePanelWidth"
      hide-overlay
      class="ml-14"
    >
      <ts-scenario
        :scenario="scenario"
        :minimize-panel="minimizeRightSidePanel"
        @togglePanel="minimizeRightSidePanel = !minimizeRightSidePanel"
      ></ts-scenario>
    </v-navigation-drawer>

    <!-- Search -->
    <v-row>
      <v-col cols="12">
        <v-card outlined class="pa-md-3 pb-3">
          <v-row>
            <v-col cols="12">
              <v-card class="d-flex align-start" flat>
                <v-sheet class="mt-1">
                  <ts-search-history-buttons @toggleSearchHistory="toggleSearchHistory()"></ts-search-history-buttons>
                </v-sheet>
                <v-divider vertical class="mx-2"></v-divider>

                <v-menu
                  v-model="showSearchDropdown"
                  offset-y
                  attach
                  :close-on-content-click="false"
                  :close-on-click="true"
                >
                  <template v-slot:activator="{ on, attrs }">
                    <v-text-field
                      v-model="currentQueryString"
                      hide-details
                      label="Search"
                      placeholder="Search"
                      single-line
                      dense
                      filled
                      flat
                      solo
                      append-icon="mdi-magnify"
                      id="tsSearchInput"
                      @keyup.enter="search"
                      @click="showSearchDropdown = true"
                      ref="searchInput"
                      v-bind="attrs"
                      v-on="on"
                    >
                    </v-text-field>
                  </template>

                  <ts-search-dropdown
                    v-click-outside="onClickOutside"
                    :selected-labels="selectedLabels"
                    :query-string="currentQueryString"
                    @setActiveView="searchView"
                    @addChip="addChip"
                    @updateLabelChips="updateLabelChips()"
                    @close-on-click="showSearchDropdown = false"
                    @node-click="jumpInHistory"
                    @setQueryAndFilter="setQueryAndFilter"
                  >
                  </ts-search-dropdown>
                </v-menu>
              </v-card>
            </v-col>
          </v-row>
          <v-divider class="mt-2 mb-3"></v-divider>

          <!-- Timeline picker -->
          <v-row dense>
            <v-col cols="12">
              <ts-timeline-picker
                @updateSelectedTimelines="updateSelectedTimelines($event)"
                :current-query-filter="currentQueryFilter"
                :count-per-index="eventList.meta.count_per_index"
                :count-per-timeline="eventList.meta.count_per_timeline"
              ></ts-timeline-picker>
            </v-col>
          </v-row>

          <!-- Time filter chips -->
          <v-row dense>
            <v-col cols="12" class="py-0">
              <v-chip-group>
                <span v-for="(chip, index) in timeFilterChips" :key="index + chip.value">
                  <v-menu offset-y content-class="menu-with-gap">
                    <template v-slot:activator="{ on }">
                      <v-chip outlined v-on="on">
                        <v-icon left small> mdi-clock-outline </v-icon>
                        <span
                          v-bind:style="[!chip.active ? { 'text-decoration': 'line-through', opacity: '50%' } : '']"
                        >
                          <span>{{ chip.value.split(',')[0] }}</span>
                          <span
                            v-if="
                              chip.type === 'datetime_range' && chip.value.split(',')[0] !== chip.value.split(',')[1]
                            "
                          >
                            &rarr; {{ chip.value.split(',')[1] }}</span
                          >
                        </span>
                      </v-chip>
                    </template>
                    <v-card>
                      <v-list>
                        <v-list-item>
                          <v-list-item-action>
                            <v-icon>mdi-square-edit-outline</v-icon>
                          </v-list-item-action>
                          <v-list-item-subtitle>Edit filter</v-list-item-subtitle>
                        </v-list-item>

                        <v-list-item @click="toggleChip(chip)">
                          <v-list-item-action>
                            <v-icon v-if="chip.active">mdi-eye-off</v-icon>
                            <v-icon v-else>mdi-eye</v-icon>
                          </v-list-item-action>
                          <v-list-item-subtitle
                            ><span v-if="chip.active">Temporarily disable</span
                            ><span v-else>Re-enable</span></v-list-item-subtitle
                          >
                        </v-list-item>
                        <v-list-item @click="removeChip(chip)">
                          <v-list-item-action>
                            <v-icon>mdi-delete</v-icon>
                          </v-list-item-action>
                          <v-list-item-subtitle>Remove filter</v-list-item-subtitle>
                        </v-list-item>
                      </v-list>
                    </v-card>
                  </v-menu>
                  <v-btn v-if="index + 1 < timeFilterChips.length" icon small style="margin-top: 2px" class="mr-2"
                    >OR</v-btn
                  >
                </span>
                <span>
                  <v-menu
                    v-model="timeFilterMenu"
                    offset-y
                    :close-on-content-click="false"
                    :close-on-click="true"
                    content-class="menu-with-gap"
                    allow-overflow
                    style="overflow: visible"
                  >
                    <template v-slot:activator="{ on, attrs }">
                      <v-chip outlined v-bind="attrs" v-on="on">
                        <v-icon left small> mdi-clock-plus-outline </v-icon>
                        Add timefilter
                      </v-chip>
                    </template>

                    <ts-filter-menu app @cancel="timeFilterMenu = false" @addChip="addChip"></ts-filter-menu>
                  </v-menu>
                </span>

                <span>
                  <v-menu
                    v-model="addManualEvent"
                    offset-y
                    :close-on-content-click="false"
                    :close-on-click="true"
                    content-class="menu-with-gap"
                    allow-overflow
                    style="overflow: visible"
                  >
                    <template v-slot:activator="{ on, attrs }">
                      <v-chip outlined v-bind="attrs" v-on="on">
                        <v-icon left small> mdi-braille </v-icon>
                        Add manual event
                      </v-chip>
                    </template>
                    <ts-add-manual-event
                      app
                      @cancel="addManualEvent = false"
                      :datetimeProp="datetimeManualEvent"
                    ></ts-add-manual-event>
                  </v-menu>
                </span>
              </v-chip-group>
            </v-col>
          </v-row>

          <!-- Term filters -->
          <v-row dense v-if="filterChips.length">
            <v-col cols="12" class="py-0">
              <v-chip-group>
                <span v-for="(chip, index) in filterChips" :key="index + chip.value">
                  <v-chip>
                    {{ chip.value | formatLabelText }}
                  </v-chip>
                  <v-btn v-if="index + 1 < timeFilterChips.length" icon small style="margin-top: 2px" class="mr-2"
                    >AND</v-btn
                  >
                </span>
              </v-chip-group>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>

    <!-- Search History -->
    <v-row>
      <v-col v-show="showSearchHistory" cols="12">
        <v-card outlined>
          <v-toolbar elevation="0" dense>
            <v-toolbar-title>Search history</v-toolbar-title>
            <v-spacer></v-spacer>

            <v-slider
              v-model="zoomLevel"
              thumb-label
              ticks
              append-icon="mdi-magnify-plus-outline"
              prepend-icon="mdi-magnify-minus-outline"
              min="0.1"
              max="1"
              step="0.1"
              class="mt-6"
            >
              <template v-slot:thumb-label="{ value }"> {{ value * 100 }}% </template>
            </v-slider>

            <v-btn icon @click="showSearchHistory = false" class="ml-4">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-toolbar>
          <div
            v-dragscroll
            class="pa-md-4 no-scrollbars"
            style="overflow: scroll; white-space: nowrap; max-height: 500px; min-height: 500px"
          >
            <ts-search-history-tree
              @node-click="jumpInHistory"
              :show-history="showSearchHistory"
              v-bind:style="{ transform: 'scale(' + zoomLevel + ')' }"
              style="transform-origin: top left"
            ></ts-search-history-tree>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Eventlist -->
    <v-row>
      <v-col
        cols="12"
        v-if="(!eventList.objects.length && !searchInProgress) || !this.currentQueryFilter.indices.length"
      >
        <v-card outlined class="pa-4">
          <p>
            Your search <span v-if="currentQueryString">"{{ currentQueryString }}"</span> did not match any events.
          </p>
          <p>Suggestions:</p>
          <li>Try different keywords.</li>
          <li>Try more general keywords.</li>
          <li>Try fewer keywords.</li>
        </v-card>
      </v-col>

      <v-col cols="12" v-if="eventList.objects.length || (searchInProgress && this.currentQueryFilter.indices.length)">
        <v-card flat>
          <v-toolbar flat>
            <v-card-text>
              {{ fromEvent }}-{{ toEvent }} of {{ totalHits }} events ({{ totalTime }}s)

              <v-dialog v-model="saveSearchMenu" width="500">
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon v-bind="attrs" v-on="on">
                    <v-icon>mdi-content-save-outline</v-icon>
                  </v-btn>
                </template>

                <v-card>
                  <v-card-title> Save Search </v-card-title>

                  <v-card-text>
                    <v-text-field v-model="saveSearchFormName" required placeholder="Name your saved search">
                    </v-text-field>
                  </v-card-text>

                  <v-divider></v-divider>

                  <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="primary" text @click="saveSearchMenu = false"> Cancel </v-btn>
                    <v-btn color="primary" text @click="saveSearch" :disabled="!saveSearchFormName"> Save </v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>
            </v-card-text>

            <v-spacer></v-spacer>

            <v-btn icon @click="showHistogram = !showHistogram">
              <v-icon>mdi-chart-bar</v-icon>
            </v-btn>

            <v-btn icon>
              <v-icon>mdi-view-column-outline</v-icon>
            </v-btn>

            <v-menu offset-y :close-on-content-click="false">
              <template v-slot:activator="{ on, attrs }">
                <v-btn icon v-bind="attrs" v-on="on">
                  <v-icon>mdi-dots-vertical</v-icon>
                </v-btn>
              </template>

              <v-card outlined max-width="475" class="mx-auto">
                <v-list subheader two-line flat dense>
                  <v-subheader>Density</v-subheader>

                  <v-list-item-group>
                    <v-list-item :ripple="false">
                      <template>
                        <v-list-item-action>
                          <v-radio-group v-model="displayOptions.isCompact">
                            <v-radio :value="false"></v-radio>
                          </v-radio-group>
                        </v-list-item-action>

                        <v-list-item-content>
                          <v-list-item-title>Comfortable</v-list-item-title>
                          <v-list-item-subtitle>More space between rows</v-list-item-subtitle>
                        </v-list-item-content>
                      </template>
                    </v-list-item>

                    <v-list-item :ripple="false">
                      <template>
                        <v-list-item-action>
                          <v-radio-group v-model="displayOptions.isCompact">
                            <v-radio :value="true"></v-radio>
                          </v-radio-group>
                        </v-list-item-action>

                        <v-list-item-content>
                          <v-list-item-title>Compact</v-list-item-title>
                          <v-list-item-subtitle>Less space between rows</v-list-item-subtitle>
                        </v-list-item-content>
                      </template>
                    </v-list-item>
                  </v-list-item-group>
                  <v-divider></v-divider>

                  <v-list subheader two-line flat>
                    <v-subheader>Misc</v-subheader>
                    <v-list-item-group>
                      <v-list-item :ripple="false">
                        <v-list-item-action>
                          <v-switch dense color="" v-model="displayOptions.showTags"></v-switch>
                        </v-list-item-action>
                        <v-list-item-content>
                          <v-list-item-title>Tags</v-list-item-title>
                          <v-list-item-subtitle>Show tags</v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list-item-group>
                    <v-list-item-group>
                      <v-list-item :ripple="false">
                        <v-list-item-action>
                          <v-switch dense v-model="displayOptions.showEmojis"></v-switch>
                        </v-list-item-action>
                        <v-list-item-content>
                          <v-list-item-title>Emojis</v-list-item-title>
                          <v-list-item-subtitle>Show emojis</v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list-item-group>
                  </v-list>
                </v-list>
              </v-card>
            </v-menu>
          </v-toolbar>

          <v-sheet class="pa-4">
            <v-card class="pa-2" outlined v-if="showHistogram">
              <ts-bar-chart
                :chart-data="eventList.meta.count_over_time"
                @addChip="addChipFromHistogram($event)"
              ></ts-bar-chart>
            </v-card>
          </v-sheet>

          <v-data-table
            v-model="selectedEvents"
            :headers="headers"
            :items="eventList.objects"
            :footer-props="{ 'items-per-page-options': [10, 40, 80, 100, 200, 500], 'show-current-page': true }"
            :loading="searchInProgress"
            :options.sync="tableOptions"
            :server-items-length="totalHits"
            item-key="_id"
            loading-text="Searching... Please wait"
            show-select
            disable-filtering
            disable-sort
            :expanded="expandedRows"
            :dense="displayOptions.isCompact"
          >
            <template v-slot:top="{ pagination, options, updateOptions }">
              <v-data-footer
                :pagination="pagination"
                :options="options"
                @update:options="updateOptions"
                :show-current-page="true"
                :items-per-page-options="[10, 40, 80, 100, 200, 500]"
              ></v-data-footer>
            </template>
            <!-- Event details -->
            <template v-slot:expanded-item="{ headers, item }">
              <td :colspan="headers.length">
                <!-- Details -->
                <v-container v-if="item.showDetails" fluid class="mt-4">
                  <ts-event-detail :event="item"></ts-event-detail>
                </v-container>

                <!-- Time bubble -->
                <v-divider v-if="item.showDetails && item.deltaDays"></v-divider>
                <div v-if="item.deltaDays > 0" class="ml-16">
                  <div
                    class="ts-time-bubble-vertical-line ts-time-bubble-vertical-line-color"
                    v-bind:style="getTimeBubbleColor(item)"
                  ></div>
                  <div class="ts-time-bubble ts-time-bubble-color" v-bind:style="getTimeBubbleColor(item)">
                    <h5>
                      <b>{{ item.deltaDays | compactNumber }}</b
                      ><br />days
                    </h5>
                  </div>
                  <div
                    class="ts-time-bubble-vertical-line ts-time-bubble-vertical-line-color"
                    v-bind:style="getTimeBubbleColor(item)"
                  ></div>
                </div>
              </td>
            </template>

            <!-- Datetime field with action buttons -->
            <template v-slot:item._source.timestamp="{ item }">
              <div v-bind:style="getTimelineColor(item)" class="datetime-table-cell">
                {{ item._source.timestamp | formatTimestamp | toISO8601 }}
              </div>
            </template>

            <!-- Actions field -->
            <template v-slot:item.actions="{ item }">
              <v-btn small icon>
                <v-icon>mdi-star-outline</v-icon>
              </v-btn>
              <v-btn small icon>
                <v-icon>mdi-tag-plus-outline</v-icon>
              </v-btn>
              <v-btn small icon @click="addEventBtn(item._source.datetime)">
                <v-icon>mdi-braille</v-icon>
              </v-btn>
            </template>

            <!-- Message field -->
            <template v-slot:item._source.message="{ item }">
              <span class="ts-event-field-container" style="cursor: pointer" @click="toggleDetailedEvent(item)">
                <span class="ts-event-field-ellipsis">
                  <!-- Tags -->
                  <span v-if="displayOptions.showTags">
                    <v-chip small label outlined class="mr-2" v-for="tag in item._source.tag" :key="tag">{{
                      tag
                    }}</v-chip>
                  </span>
                  <!-- Emojis -->
                  <span v-if="displayOptions.showEmojis">
                    <span
                      class="mr-2"
                      v-for="emoji in item._source.__ts_emojis"
                      :key="emoji"
                      v-html="emoji"
                      :title="meta.emojis[emoji]"
                      >{{ emoji }}
                    </span>
                  </span>
                  <span>{{ item._source.message }}</span>
                </span>
              </span>
            </template>

            <!-- Timeline name field -->
            <template v-slot:item.timeline_name="{ item }">
              <v-chip label style="margin-top: 1px; margin-bottom: 1px; font-size: 0.9em">{{
                getTimeline(item).name
              }}</v-chip>
            </template>

            <!-- Comment field -->
            <template v-slot:item._source.comment="{ item }">
              <v-badge
                :offset-y="16"
                bordered
                v-if="item._source.comment.length"
                :content="item._source.comment.length"
              >
                <v-icon @click="toggleDetailedEvent(item)"> mdi-comment-text-multiple-outline </v-icon>
              </v-badge>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

import TsSearchHistoryTree from '../components/Explore/SearchHistoryTree'
import TsSearchHistoryButtons from '../components/Explore/SearchHistoryButtons'
import TsSearchDropdown from '../components/Explore/SearchDropdown'
import TsBarChart from '../components/Explore/BarChart'
import TsTimelinePicker from '../components/Explore/TimelinePicker'
import TsFilterMenu from '../components/Explore/FilterMenu'
import TsAddManualEvent from '../components/Explore/AddManualEvent'
import TsScenario from '../components/Scenarios/Scenario'
import TsEventDetail from '../components/Explore/EventDetail'

import EventBus from '../main'
import { None } from 'vega'

import { dragscroll } from 'vue-dragscroll'

const defaultQueryFilter = () => {
  return {
    from: 0,
    terminate_after: 40,
    size: 40,
    indices: [],
    order: 'asc',
    chips: [],
  }
}

const emptyEventList = () => {
  return {
    meta: {
      count_per_index: {},
    },
    objects: [],
  }
}

export default {
  directives: {
    dragscroll,
  },
  components: {
    TsSearchHistoryTree,
    TsSearchHistoryButtons,
    TsSearchDropdown,
    TsBarChart,
    TsTimelinePicker,
    TsFilterMenu,
    TsAddManualEvent,
    TsScenario,
    TsEventDetail,
  },
  props: ['sketchId'],
  data() {
    return {
      headers: [
        { text: '', value: 'data-table-select' },

        {
          text: 'Datetime (UTC)',
          align: 'start',
          value: '_source.timestamp',
          width: '230',
        },
        {
          value: 'actions',
          width: '90',
        },
        {
          text: 'Message',
          align: 'start',
          value: '_source.message',
          width: '100%',
        },
        {
          value: '_source.comment',
          align: 'end',
        },
        {
          value: 'timeline_name',
          align: 'end',
        },
      ],
      tableOptions: {
        itemsPerPage: 40,
      },
      currentItemsPerPage: 40,
      drawer: false,
      leftDrawer: true,
      expandedRows: [],
      timeFilterMenu: false,
      addManualEvent: false,
      saveSearchMenu: false,
      saveSearchFormName: '',
      fromSavedSearch: false,
      datetimeManualEvent: '', // datetime of an event used
      // old stuff
      params: {},
      showCreateViewModal: false,
      showFilterCard: true,
      showSearch: true,
      searchInProgress: false,
      currentPage: 1,
      contextEvent: false,
      originalContext: false,
      isFullPage: true,
      loadingComponent: null,
      showSearchDropdown: false,
      eventList: {
        meta: {},
        objects: [],
      },
      currentQueryString: '',
      currentQueryFilter: defaultQueryFilter(),
      selectedFields: [{ field: 'message', type: 'text' }],
      selectedFieldsProxy: [],
      expandFieldDropdown: false,
      selectedEvents: [],
      displayOptions: {
        isCompact: false,
        showTags: true,
        showEmojis: true,
        showMillis: false,
      },
      selectedLabels: [],
      showSearchHistory: false,
      showHistogram: false,
      branchParent: None,
      zoomLevel: 0.7,
      zoomOrigin: {
        x: 0,
        y: 0,
      },
      minimizeRightSidePanel: false,
      sidePanelTab: null,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    scenario() {
      return this.$store.state.scenario
    },
    totalHits() {
      return this.eventList.meta.es_total_count_complete || 0
    },
    totalTime() {
      return this.eventList.meta.es_time / 1000 || 0
    },
    fromEvent() {
      return this.currentQueryFilter.from || 1
    },
    toEvent() {
      if (this.totalHits < this.currentQueryFilter.size) {
        return
      }
      return parseInt(this.currentQueryFilter.from) + parseInt(this.currentQueryFilter.size)
    },
    numSelectedEvents() {
      return this.selectedEvents.length
    },
    filterChips: function () {
      return this.currentQueryFilter.chips.filter((chip) => chip.type === 'label' || chip.type === 'term')
    },
    timeFilterChips: function () {
      return this.currentQueryFilter.chips.filter((chip) => chip.type.startsWith('datetime'))
    },
    filteredLabels() {
      return this.$store.state.meta.filter_labels.filter((label) => !label.label.startsWith('__'))
    },
    currentSearchNode() {
      return this.$store.state.currentSearchNode
    },
    rightSidePanelWidth() {
      let width = '430'
      if (this.minimizeRightSidePanel) {
        width = '50'
      }
      return width
    },
  },
  methods: {
    addEventBtn: function (datetimeManualEvent) {
      this.datetimeManualEvent = datetimeManualEvent
      this.addManualEvent = true
    },
    toggleSearchHistory: function () {
      this.showSearchHistory = !this.showSearchHistory
      if (this.showSearchHistory) {
        this.triggerScrollTo()
      }
    },
    toggleDetailedEvent: function (row) {
      let index = this.expandedRows.findIndex((x) => x._id === row._id)
      if (this.expandedRows.some((event) => event._id === row._id)) {
        if (row.showDetails) {
          row['showDetails'] = false
          this.expandedRows.splice(index, 1)
        } else {
          row['showDetails'] = true
          this.expandedRows.splice(index, 1)
          this.expandedRows.push(row)
          return
        }

        if (row.deltaDays) {
          this.expandedRows.splice(index, 1)
          this.expandedRows.push(row)
        }
      } else {
        row['showDetails'] = true
        this.expandedRows.push(row)
      }
    },
    addTimeBubbles: function () {
      this.expandedRows = []
      this.eventList.objects.forEach((event, index) => {
        if (index < 1) {
          return
        }
        let prevEvent = this.eventList.objects[index - 1]
        let timestampMillis = this.$options.filters.formatTimestamp(event._source.timestamp)
        let prevTimestampMillis = this.$options.filters.formatTimestamp(prevEvent._source.timestamp)
        let timestamp = Math.floor(timestampMillis / 1000)
        let prevTimestamp = Math.floor(prevTimestampMillis / 1000)
        let delta = Math.floor(timestamp - prevTimestamp)
        if (this.order === 'desc') {
          delta = Math.floor(prevTimestamp - timestamp)
        }
        let deltaDays = Math.floor(delta / 60 / 60 / 24)
        if (deltaDays > 0) {
          prevEvent['deltaDays'] = deltaDays
          this.expandedRows.push(prevEvent)
        }
      })
    },
    getTimeline: function (event) {
      let isLegacy = this.meta.indices_metadata[event._index].is_legacy
      let timeline
      if (isLegacy) {
        timeline = this.sketch.active_timelines.filter(
          (timeline) => timeline.searchindex.index_name === event._index
        )[0]
      } else {
        timeline = this.sketch.active_timelines.filter((timeline) => timeline.id === event._source.__ts_timeline_id)[0]
      }
      return timeline
    },
    getTimelineColor(event) {
      let timeline = this.getTimeline(event)
      let backgroundColor = timeline.color
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
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
      }
    },
    getTimeBubbleColor() {
      let backgroundColor = '#f5f5f5'
      if (this.$vuetify.theme.dark) {
        backgroundColor = '#333'
      }
      return {
        'background-color': backgroundColor,
      }
    },
    search: function (emitEvent = true, resetPagination = true, incognito = false, parent = false) {
      // Remove URL parameter if new search is executed after saved search
      if (this.fromSavedSearch) {
        this.fromSavedSearch = false
      } else {
        this.$router.push(this.$route.path)
      }

      if (!this.currentQueryString) {
        return
      }
      this.searchInProgress = true

      if (this.contextEvent) {
        // Scroll to the context box in the UI
        this.$scrollTo('#context', 200, { offset: -300 })
      }

      this.selectedEvents = []
      this.eventList = emptyEventList()

      if (resetPagination) {
        // TODO: Can we keep position of the pagination when changing page size?
        // We need to calculate the new position in the page range and it is not
        // trivial with the current pagination UI component we use.
        this.currentQueryFilter.from = 0
      }

      // Update with selected fields
      this.currentQueryFilter.fields = this.selectedFields

      let formData = {
        query: this.currentQueryString,
        filter: this.currentQueryFilter,
      }

      // Search history
      if (incognito) {
        formData['incognito'] = true
      }

      if (parent) {
        formData['parent'] = parent
      }

      if (parent && incognito) {
        this.branchParent = parent
      }

      if (this.branchParent) {
        formData['parent'] = this.branchParent
      }

      if (emitEvent) {
        EventBus.$emit('newSearch')
        this.showSearchDropdown = false
      }

      ApiClient.search(this.sketchId, formData)
        .then((response) => {
          this.eventList.objects = response.data.objects
          this.eventList.meta = response.data.meta
          this.searchInProgress = false

          this.addTimeBubbles()

          if (!incognito) {
            EventBus.$emit('createBranch', this.eventList.meta.search_node)
            this.$store.dispatch('updateSearchHistory')
            this.branchParent = this.eventList.meta.search_node.id
          }
        })
        .catch((e) => {})
    },
    setQueryAndFilter: function (searchEvent) {
      this.currentQueryString = searchEvent.queryString
      this.currentQueryFilter = searchEvent.queryFilter
      // Preserve user defined item count instead of resetting.
      this.currentQueryFilter.size = this.currentItemsPerPage
      this.currentQueryFilter.terminate_after = this.currentItemsPerPage
      if (searchEvent.doSearch) {
        this.search()
      }
    },
    exportSearchResult: function () {
      let formData = {
        query: this.currentQueryString,
        filter: this.currentQueryFilter,
        file_name: 'export.zip',
      }
      ApiClient.exportSearchResult(this.sketchId, formData)
        .then((response) => {
          let fileURL = window.URL.createObjectURL(new Blob([response.data]))
          let fileLink = document.createElement('a')
          let fileName = 'export.zip'
          fileLink.href = fileURL
          fileLink.setAttribute('download', fileName)
          document.body.appendChild(fileLink)
          fileLink.click()
          this.loadingClose()
        })
        .catch((e) => {
          console.error(e)
        })
    },
    searchView: function (viewId) {
      this.selectedEvents = []
      this.showSearchDropdown = false
      this.fromSavedSearch = true

      if (viewId !== parseInt(viewId, 10) && typeof viewId !== 'string') {
        viewId = viewId.id
        this.$router.push({ name: 'Explore', query: { view: viewId } })
      }
      ApiClient.getView(this.sketchId, viewId)
        .then((response) => {
          let view = response.data.objects[0]
          this.currentQueryString = view.query_string
          this.currentQueryFilter = JSON.parse(view.query_filter)
          if (!this.currentQueryFilter.fields || !this.currentQueryFilter.fields.length) {
            this.currentQueryFilter.fields = [{ field: 'message', type: 'text' }]
          }
          this.selectedFields = this.currentQueryFilter.fields
          if (this.currentQueryFilter.indices[0] === '_all' || this.currentQueryFilter.indices === '_all') {
            let allIndices = []
            this.sketch.active_timelines.forEach((timeline) => {
              let isLegacy = this.meta.indices_metadata[timeline.searchindex.index_name].is_legacy
              if (isLegacy) {
                allIndices.push(timeline.searchindex.index_name)
              } else {
                allIndices.push(timeline.id)
              }
            })
            this.currentQueryFilter.indices = allIndices
          }
          let chips = this.currentQueryFilter.chips
          if (chips) {
            for (let i = 0; i < chips.length; i++) {
              if (chips[i].type === 'label') {
                this.selectedLabels.push(chips[i].value)
              }
            }
          }
          this.contextEvent = false
          this.search(false)
        })
        .catch((e) => {})
    },
    searchContext: function (event) {
      // TODO: Make this selectable in the UI
      const contextTime = 300
      const numContextEvents = 500

      this.contextEvent = event
      if (!this.originalContext) {
        let currentQueryStringCopy = JSON.parse(JSON.stringify(this.currentQueryString))
        let currentQueryFilterCopy = JSON.parse(JSON.stringify(this.currentQueryFilter))
        this.originalContext = { queryString: currentQueryStringCopy, queryFilter: currentQueryFilterCopy }
      }

      const dateTimeTemplate = 'YYYY-MM-DDTHH:mm:ss'
      let startDateTimeMoment = this.$moment.utc(this.contextEvent._source.datetime)
      let newStartDate = startDateTimeMoment.clone().subtract(contextTime, 's').format(dateTimeTemplate)
      let newEndDate = startDateTimeMoment.clone().add(contextTime, 's').format(dateTimeTemplate)
      let startChip = {
        field: '',
        value: newStartDate + ',' + startDateTimeMoment.format(dateTimeTemplate),
        type: 'datetime_range',
        operator: 'must',
        active: true,
      }
      let endChip = {
        field: '',
        value: startDateTimeMoment.format(dateTimeTemplate) + ',' + newEndDate,
        type: 'datetime_range',
        operator: 'must',
        active: true,
      }
      // TODO: Use chips instead
      this.currentQueryString = '* OR ' + '_id:' + this.contextEvent._id

      this.currentQueryFilter.chips = [startChip, endChip]

      let isLegacy = this.meta.indices_metadata[this.contextEvent._index].is_legacy
      if (isLegacy) {
        this.currentQueryFilter.indices = [this.contextEvent._index]
      } else {
        this.currentQueryFilter.indices = [this.contextEvent._source.__ts_timeline_id]
      }
      this.currentQueryFilter.size = numContextEvents

      this.search()
    },
    removeContext: function () {
      this.contextEvent = false
      this.currentQueryString = JSON.parse(JSON.stringify(this.originalContext.queryString))
      this.currentQueryFilter = JSON.parse(JSON.stringify(this.originalContext.queryFilter))
      this.search()
    },
    updateSelectedTimelines: function (timelines) {
      let selected = []
      timelines.forEach((timeline) => {
        let isLegacy = this.meta.indices_metadata[timeline.searchindex.index_name].is_legacy
        if (isLegacy) {
          selected.push(timeline.searchindex.index_name)
        } else {
          selected.push(timeline.id)
        }
      })
      this.currentQueryFilter.indices = selected
      this.search()
    },
    clearSearch: function () {
      this.currentQueryString = ''
      this.currentQueryFilter = defaultQueryFilter()
      this.currentQueryFilter.indices = '_all'
      this.eventList = emptyEventList()
      this.$router.replace({ query: null })
    },
    toggleChip: function (chip) {
      // Treat undefined as active to support old chip formats.
      if (chip.active === undefined) {
        chip.active = true
      }
      chip.active = !chip.active
      this.search()
    },
    removeChip: function (chip, search = true) {
      let chipIndex = this.currentQueryFilter.chips.findIndex((c) => c.value === chip.value)
      this.currentQueryFilter.chips.splice(chipIndex, 1)
      if (chip.type === 'label') {
        this.selectedLabels = this.selectedLabels.filter((label) => label !== chip.value)
      }
      if (search) {
        this.search()
      }
    },
    updateChip: function (newChip, oldChip) {
      // Replace the chip at the given index
      let chipIndex = this.currentQueryFilter.chips.findIndex(
        (c) => c.value === oldChip.value && c.type === oldChip.type
      )
      this.currentQueryFilter.chips.splice(chipIndex, 1, newChip)
      this.search()
    },
    addChip: function (chip) {
      // Legacy views don't support chips so we need to add an array in order
      // to upgrade the view to the new filter system.
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = []
      }
      this.currentQueryFilter.chips.push(chip)
      this.search()
    },
    addChipFromHistogram: function (chip) {
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = []
      }
      this.currentQueryFilter.chips.forEach((chip) => {
        if (chip.type === 'datetime_range') {
          this.removeChip(chip, false)
        }
      })
      this.addChip(chip)
    },

    toggleLabelChip: function (labelName) {
      let chip = {
        field: '',
        value: labelName,
        type: 'label',
        operator: 'must',
        active: true,
      }
      let chips = this.currentQueryFilter.chips
      if (chips) {
        for (let i = 0; i < chips.length; i++) {
          if (chips[i].value === labelName) {
            this.removeChip(i)
            return
          }
        }
      }
      this.addChip(chip)
    },
    updateLabelChips: function () {
      // Remove all current label chips
      this.currentQueryFilter.chips = this.currentQueryFilter.chips.filter((chip) => chip.type !== 'label')
      this.selectedLabels.forEach((label) => {
        let chip = {
          field: '',
          value: label,
          type: 'label',
          operator: 'must',
          active: true,
        }
        this.addChip(chip)
        this.showSearchDropdown = false
      })
    },
    updateLabelList: function (label) {
      if (this.meta.filter_labels.indexOf(label) === -1) {
        this.meta.filter_labels.push(label)
      }
    },
    paginate: function () {
      // Reset pagination if number of pages per page changes.
      if (this.tableOptions.itemsPerPage !== this.currentItemsPerPage) {
        this.tableOptions.page = 1
        this.currentPage = 1
        this.currentItemsPerPage = this.tableOptions.itemsPerPage
        this.currentQueryFilter.size = this.tableOptions.itemsPerPage
        this.search(true, true, true)
        return
      }
      // To avoid double search request exit early if this is the first search for this
      // search session.
      if (this.currentPage === this.tableOptions.page) {
        return
      }
      this.currentQueryFilter.from =
        this.tableOptions.page * this.currentQueryFilter.size - this.currentQueryFilter.size
      this.currentPage = this.tableOptions.page
      this.search(true, false, true)
    },
    updateSelectedFields: function (value) {
      // If we haven't fetched the field before, do an new search.
      value.forEach((field) => {
        if (!this.selectedFields.filter((e) => e.field === field.field).length > 0) {
          this.search(true, true, true)
        }
      })
      value.forEach((field) => {
        this.selectedFields.push(field)
      })
      // Prevents tags from being displayed
      this.selectedFieldsProxy = []
    },
    removeField: function (index) {
      this.selectedFields.splice(index, 1)
    },
    toggleStar: function () {
      let eventsToToggle = []
      Object.keys(this.selectedEvents).forEach((key, index) => {
        eventsToToggle.push(this.selectedEvents[key])
      })
      ApiClient.saveEventAnnotation(this.sketch.id, 'label', '__ts_star', eventsToToggle, this.currentSearchNode)
        .then((response) => {})
        .catch((e) => {})

      EventBus.$emit('toggleStar', this.selectedEvents)
    },
    changeSortOrder: function () {
      if (this.currentQueryFilter.order === 'asc') {
        this.currentQueryFilter.order = 'desc'
      } else {
        this.currentQueryFilter.order = 'asc'
      }
      this.search(true, true, true)
    },
    loadingOpen: function () {
      this.loadingComponent = this.$buefy.loading.open({
        container: this.isFullPage ? null : this.$refs.element.$el,
      })
    },
    loadingClose: function () {
      this.loadingComponent.close()
    },
    jumpInHistory: function (node) {
      this.currentQueryString = node.query_string
      this.currentQueryFilter = JSON.parse(node.query_filter)
      if (!this.currentQueryFilter.fields || !this.currentQueryFilter.fields.length) {
        this.currentQueryFilter.fields = [{ field: 'message', type: 'text' }]
      }
      this.selectedFields = this.currentQueryFilter.fields
      if (this.currentQueryFilter.indices[0] === '_all' || this.currentQueryFilter.indices === '_all') {
        let allIndices = []
        this.sketch.active_timelines.forEach((timeline) => {
          let isLegacy = this.meta.indices_metadata[timeline.searchindex.index_name].is_legacy
          if (isLegacy) {
            allIndices.push(timeline.searchindex.index_name)
          } else {
            allIndices.push(timeline.id)
          }
        })
        this.currentQueryFilter.indices = allIndices
      }
      let chips = this.currentQueryFilter.chips
      if (chips) {
        for (let i = 0; i < chips.length; i++) {
          if (chips[i].type === 'label') {
            this.selectedLabels.push(chips[i].value)
          }
        }
      }
      this.contextEvent = false
      this.search(false, true, true, node.id)
    },
    triggerScrollTo: function () {
      EventBus.$emit('triggerScrollTo')
    },
    zoomWithMouse: function (event) {
      // Add @wheel="zoomWithMouse" on element to activate.
      this.zoomOrigin.x = event.pageX
      this.zoomOrigin.y = event.pageY
      if (event.deltaY < 0) {
        this.zoomLevel += 0.07
      } else if (event.deltaY > 0) {
        this.zoomLevel -= 0.07
      }
    },
    closeSearchDropdown: function (targetElement) {
      // Prevent dropdown to close when the search input field is clicked.
      if (targetElement !== this.$refs.searchInput && targetElement.getAttribute('data-explore-element') === null) {
        this.showSearchDropdown = false
      }
    },
    onClickOutside: function (e) {
      if (e.target.id !== 'tsSearchInput') {
        this.showSearchDropdown = false
      }
    },
    saveSearch: function () {
      ApiClient.createView(this.sketchId, this.saveSearchFormName, this.currentQueryString, this.currentQueryFilter)
        .then((response) => {
          this.saveSearchFormName = ''
          this.saveSearchMenu = false
          let newView = response.data.objects[0]
          this.$store.state.meta.views.push(newView)
          this.$router.push({ name: 'Explore', query: { view: newView.id } })
        })
        .catch((e) => {})
    },
  },

  watch: {
    tableOptions: {
      handler() {
        this.paginate()
      },
      deep: true,
    },
  },
  mounted() {
    this.$refs.searchInput.focus()
  },
  created: function () {
    let doSearch = false

    this.params = {
      viewId: this.$route.query.view,
      indexName: this.$route.query.timeline,
      resultLimit: this.$route.query.limit,
      queryString: this.$route.query.q,
    }

    if (this.params.viewId) {
      this.searchView(this.params.viewId)
      return
    }

    if (this.params.queryString) {
      this.currentQueryString = this.params.queryString
      doSearch = true
    }

    if (this.params.indexName) {
      if (!this.params.queryString) {
        this.currentQueryString = '*'
      }

      let timeline = this.sketch.active_timelines.find((timeline) => {
        return timeline.id === parseInt(this.params.indexName, 10)
      })

      let isLegacy = this.meta.indices_metadata[timeline.searchindex.index_name].is_legacy
      if (isLegacy) {
        this.currentQueryFilter.indices = [timeline.searchindex.index_name]
      } else {
        this.currentQueryFilter.indices = [timeline.id]
      }
      doSearch = true
    }

    if (!this.currentQueryString) {
      this.currentQueryFilter.indices = ['_all']
    }

    if (doSearch) {
      if (!this.currentQueryFilter.indices.length) {
        this.currentQueryFilter.indices = ['_all']
      }
      this.search()
    }
  },
}
</script>

<style lang="scss">
.chip-disabled {
  text-decoration: line-through;
  opacity: 0.5;
}

.chip-operator-label {
  margin-right: 7px;
  font-size: 0.7em;
  cursor: default;
}

.no-scrollbars::-webkit-scrollbar {
  display: none;
}

.no-scrollbars {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.ts-event-field-container {
  position: relative;
  max-width: 100%;
  padding: 0 !important;
  display: -webkit-flex;
  display: -moz-flex;
  display: flex;
  vertical-align: text-bottom !important;
}

.ts-event-field-ellipsis {
  position: absolute;
  white-space: nowrap;
  overflow-y: visible;
  overflow-x: hidden;
  text-overflow: ellipsis;
  -ms-text-overflow: ellipsis;
  -o-text-overflow: ellipsis;
  max-width: 100%;
  min-width: 0;
  width: 100%;
  top: 0;
  left: 0;
  margin-top: -10px;
}

.v-data-table__expanded.v-data-table__expanded__content {
  box-shadow: none !important;
}

.ts-time-bubble {
  width: 60px;
  height: 60px;
  border-radius: 30px;
  position: relative;
  margin: 0 0 0 65px;
  text-align: center;
  font-size: var(--font-size-small);
  background-color: #f5f5f5;
}

.ts-time-bubble h5 {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  margin: 0;
  opacity: 70%;
}

.ts-time-bubble-vertical-line {
  width: 2px;
  height: 15px;
  margin: 0 0 0 95px;
  background-color: #f5f5f5;
}

.datetime-table-cell {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
