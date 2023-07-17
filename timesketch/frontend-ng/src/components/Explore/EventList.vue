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
<template>
  <div>
    <div v-if="!eventList.objects.length && !searchInProgress" class="ml-3">
      <p>
        Your search <span v-if="currentQueryString">"{{ currentQueryString }}"</span> did not match any events.
      </p>
      <p>Suggestions:</p>
      <li>Try different keywords.</li>
      <li>Try more general keywords.</li>
      <li>Try fewer keywords.</li>
    </div>

    <div v-if="highlightEvent" class="mt-4">
      <strong>Showing context for event:</strong>
      <v-sheet class="d-flex flex-wrap mt-1 mb-5">
        <v-sheet class="flex-1-0">
          <span style="width: 200px" v-bind:style="getTimelineColor(highlightEvent)" class="datetime-table-cell pa-2">
            {{ highlightEvent._source.timestamp | formatTimestamp | toISO8601 }}
          </span>
        </v-sheet>

        <v-sheet class="">
          <span class="datetime-table-cell pa-2">
            {{ highlightEvent._source.message }}
          </span>
        </v-sheet>
      </v-sheet>
    </div>
    <div v-if="eventList.objects.length || searchInProgress">
      <v-data-table
        v-model="selectedEvents"
        :headers="headers"
        :items="eventList.objects"
        :footer-props="{ 'items-per-page-options': [10, 40, 80, 100, 200, 500], 'show-current-page': true }"
        :loading="searchInProgress"
        :options.sync="tableOptions"
        :server-items-length="totalHitsForPagination"
        item-key="_id"
        loading-text="Searching... Please wait"
        show-select
        disable-filtering
        must-sort
        :sort-desc.sync="sortOrderAsc"
        @update:sort-desc="sortEvents"
        sort-by="_source.timestamp"
        :hide-default-footer="totalHits < 11 || disablePagination"
        :expanded="expandedRows"
        :dense="displayOptions.isCompact"
        fixed-header
      >
        <template v-slot:top="{ pagination, options, updateOptions }">
          <v-toolbar dense flat color="transparent">
            <div v-if="!selectedEvents.length">
              <span style="display: inline-block; min-width: 200px">
                <small>{{ fromEvent }}-{{ toEvent }} of {{ totalHits }} events ({{ totalTime }}s)</small>
              </span>

              <v-dialog v-model="saveSearchMenu" v-if="!disableSaveSearch" width="500">
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon v-bind="attrs" v-on="on">
                    <v-icon>mdi-content-save-outline</v-icon>
                  </v-btn>
                </template>
                <v-card class="pa-4">
                  <h3>Save Search</h3>
                  <br />
                  <v-text-field
                    v-model="saveSearchFormName"
                    required
                    placeholder="Name your saved search"
                    outlined
                    dense
                    autofocus
                    @focus="$event.target.select()"
                  >
                  </v-text-field>
                  <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn text @click="saveSearchMenu = false"> Cancel </v-btn>
                    <v-btn text color="primary" @click="saveSearch" :disabled="!saveSearchFormName"> Save </v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>

              <v-btn icon @click="showHistogram = !showHistogram" v-if="!disableHistogram">
                <v-icon>mdi-chart-bar</v-icon>
              </v-btn>

              <v-dialog v-model="columnDialog" v-if="!disableColumns" max-width="500px" scrollable>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon v-bind="attrs" v-on="on">
                    <v-icon>mdi-view-column-outline</v-icon>
                  </v-btn>
                </template>

                <v-card height="50vh">
                  <v-card-title>Select columns</v-card-title>

                  <v-card-text>
                    <v-text-field
                      v-model="searchColumns"
                      append-icon="mdi-magnify"
                      label="Search"
                      single-line
                      hide-details
                    ></v-text-field>
                    <br />
                    <v-data-table
                      v-model="selectedFields"
                      :headers="columnHeaders"
                      :items="meta.mappings"
                      :search="searchColumns"
                      :hide-default-footer="true"
                      item-key="field"
                      disable-pagination
                      show-select
                      dense
                      @input="updateSelectedFields"
                    >
                    </v-data-table>
                  </v-card-text>

                  <v-divider></v-divider>

                  <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn text @click="selectedFields = [{ field: 'message', type: 'text' }]"> Reset </v-btn>
                    <v-btn text color="primary" @click="columnDialog = false"> Set columns </v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>

              <v-menu v-if="!disableSettings" offset-y :close-on-content-click="false">
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon v-bind="attrs" v-on="on">
                    <v-icon>mdi-dots-horizontal</v-icon>
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
                      <v-list-item-group>
                        <v-list-item :ripple="false">
                          <v-list-item-action>
                            <v-switch dense v-model="displayOptions.showTimelineName"></v-switch>
                          </v-list-item-action>
                          <v-list-item-content>
                            <v-list-item-title>Timeline name</v-list-item-title>
                            <v-list-item-subtitle>Show timeline name</v-list-item-subtitle>
                          </v-list-item-content>
                        </v-list-item>
                      </v-list-item-group>
                    </v-list>
                  </v-list>
                </v-card>
              </v-menu>
            </div>
            <div v-else>
              <small class="mr-2">Actions:</small>
              <v-btn x-small outlined @click="toggleMultipleStars()">
                <v-icon left color="amber">mdi-star</v-icon>
                Toggle star
              </v-btn>
            </div>

            <v-spacer></v-spacer>

            <v-data-footer
              v-if="totalHits > 11 && !disablePagination"
              :pagination="pagination"
              :options="options"
              @update:options="updateOptions"
              :show-current-page="true"
              :items-per-page-options="[10, 40, 80, 100, 200, 500]"
              items-per-page-text="Rows per page:"
              style="border: 0"
              class="mr-n3"
            ></v-data-footer>
          </v-toolbar>

          <v-card v-if="showHistogram" outlined class="my-3">
            <v-toolbar dense flat color="transparent">
              <v-spacer></v-spacer>
              <v-btn v-if="timeFilterChips.length" text color="primary" @click="removeChips(timeFilterChips)">
                reset
              </v-btn>
              <v-btn icon @click="showHistogram = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-toolbar>
            <ts-bar-chart
              :chart-data="eventList.meta.count_over_time"
              @addChip="addChipFromHistogram($event)"
            ></ts-bar-chart>
          </v-card>
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
            <div v-if="item.deltaDays > 0" class="ml-7">
              <div
                class="ts-time-bubble-vertical-line ts-time-bubble-vertical-line-color"
                v-bind:style="getTimeBubbleColor(item)"
              ></div>
              <div class="ts-time-bubble ts-time-bubble-color" v-bind:style="getTimeBubbleColor(item)">
                <div class="ts-time-bubble-text">
                  <b>{{ item.deltaDays | compactNumber }}</b> days
                </div>
              </div>
              <div
                class="ts-time-bubble-vertical-line ts-time-bubble-vertical-line-color"
                v-bind:style="getTimeBubbleColor(item)"
              ></div>
            </div>
          </td>
        </template>

        <!-- Actions field -->
        <template v-slot:item.actions="{ item }">
          <v-btn small icon @click="toggleStar(item)">
            <v-icon v-if="item._source.label.includes('__ts_star')" color="amber">mdi-star</v-icon>
            <v-icon v-else>mdi-star-outline</v-icon>
          </v-btn>

          <!-- Tag menu -->
          <ts-event-tag-menu :event="item"></ts-event-tag-menu>

          <!-- Action sub-menu -->
          <ts-event-action-menu :event="item" @showContextWindow="showContextWindow($event)"></ts-event-action-menu>
        </template>

        <!-- Datetime field with action buttons -->
        <template v-slot:item._source.timestamp="{ item }">
          <div v-bind:style="getTimelineColor(item)" class="datetime-table-cell">
            {{ item._source.timestamp | formatTimestamp | toISO8601 }}
          </div>
        </template>

        <!-- Generic slot for any field type. Adds tags and emojis to the first column. -->
        <template v-for="(field, index) in headers" v-slot:[getFieldName(field.text)]="{ item }">
          <div
            :key="field.text"
            class="ts-event-field-container"
            style="cursor: pointer"
            @click="toggleDetailedEvent(item)"
          >
            <span
              :class="{
                'ts-event-field-ellipsis': field.text === 'message',
                'ts-event-field-highlight': item._id === highlightEventId,
              }"
            >
              <!-- Tags -->
              <span
                v-if="
                  displayOptions.showTags &&
                  index === 3 &&
                  ('tag' in item._source ? item._source.tag.length > 0 : false)
                "
              >
                <ts-event-tags :item="item" :tagConfig="tagConfig" :showDetails="item.showDetails"></ts-event-tags>
              </span>
              <!-- Emojis -->
              <span v-if="displayOptions.showEmojis && index === 0">
                <span
                  class="mr-2"
                  v-for="emoji in item._source.__ts_emojis"
                  :key="emoji"
                  v-html="emoji"
                  :title="meta.emojis[emoji]"
                  >{{ emoji }}
                </span>
              </span>
              <span>{{ item._source[field.text] }}</span>
            </span>
          </div>
        </template>

        <!-- Timeline name field -->
        <template v-slot:item.timeline_name="{ item }">
          <v-chip label style="margin-top: 1px; margin-bottom: 1px; font-size: 0.8em">
            <span class="timeline-name-ellipsis" style="width: 130px; text-align: center">{{
              getTimeline(item).name
            }}</span></v-chip
          >
        </template>

        <!-- Comment field -->
        <template v-slot:item._source.comment="{ item }">
          <v-tooltip top open-delay="500">
            <template v-slot:activator="{ on }">
              <div v-on="on" class="d-inline-block">
                <v-btn icon small @click="toggleDetailedEvent(item)" v-if="item._source.comment.length">
                  <v-badge :offset-y="10" :offset-x="10" bordered :content="item._source.comment.length">
                    <v-icon small> mdi-comment-text-multiple-outline </v-icon>
                  </v-badge>
                </v-btn>
              </div>
            </template>
            <span v-if="!item['showDetails']">Open event &amp; comments</span>
            <span v-if="item['showDetails']">Close event &amp; comments</span>
          </v-tooltip>
          <v-tooltip
            v-if="item['showDetails'] && !item._source.comment.length && !item.showComments"
            top
            open-delay="500"
          >
            <template v-slot:activator="{ on }">
              <div v-on="on" class="d-inline-block">
                <v-btn icon small @click="newComment(item)">
                  <v-icon> mdi-comment-plus-outline </v-icon>
                </v-btn>
              </div>
            </template>
            <span>Add a comment</span>
          </v-tooltip>
          <v-tooltip
            v-if="item['showDetails'] && !item._source.comment.length && item.showComments"
            top
            open-delay="500"
          >
            <template v-slot:activator="{ on }">
              <div v-on="on" class="d-inline-block">
                <v-btn icon small @click="item.showComments = false">
                  <v-icon> mdi-comment-remove-outline </v-icon>
                </v-btn>
              </div>
            </template>
            <span>Close comments</span>
          </v-tooltip>
        </template>
      </v-data-table>
    </div>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import EventBus from '../../main'

import TsBarChart from './BarChart'
import TsEventDetail from './EventDetail'
import TsEventTagMenu from './EventTagMenu.vue'
import TsEventActionMenu from './EventActionMenu.vue'
import TsEventTags from './EventTags.vue'

const defaultQueryFilter = () => {
  return {
    from: 0,
    terminate_after: 40,
    size: 40,
    indices: ['_all'],
    order: 'asc',
    chips: [],
  }
}

const emptyEventList = () => {
  return {
    meta: {
      count_per_index: {},
      count_per_timeline: {},
    },
    objects: [],
  }
}

export default {
  components: {
    TsBarChart,
    TsEventDetail,
    TsEventTagMenu,
    TsEventActionMenu,
    TsEventTags,
  },
  props: {
    queryRequest: {
      type: Object,
      default: () => {},
    },
    itemsPerPage: {
      type: Number,
      default: 40,
    },
    disableSaveSearch: {
      type: Boolean,
      default: false,
    },
    disableHistogram: {
      type: Boolean,
      default: false,
    },
    disableColumns: {
      type: Boolean,
      default: false,
    },
    disableSettings: {
      type: Boolean,
      default: false,
    },
    disablePagination: {
      type: Boolean,
      default: false,
    },
    highlightEvent: {
      type: Object,
      default: () => {},
    },
  },
  data() {
    return {
      columnHeaders: [
        {
          text: '',
          value: 'field',
        },
      ],
      tableOptions: {
        itemsPerPage: this.itemsPerPage,
      },
      currentItemsPerPage: this.itemsPerPage,
      expandedRows: [],
      selectedFields: [{ field: 'message', type: 'text' }],
      searchColumns: '',
      columnDialog: false,
      saveSearchMenu: false,
      saveSearchFormName: '',
      selectedEventTags: [],
      tagConfig: {
        good: { color: 'green', textColor: 'white', label: 'mdi-check-circle-outline' },
        bad: { color: 'red', textColor: 'white', label: 'mdi-alert-circle-outline' },
        suspicious: { color: 'orange', textColor: 'white', label: 'mdi-help-circle-outline' },
      },
      searchInProgress: false,
      currentPage: 1,
      eventList: {
        meta: {},
        objects: [],
      },
      currentQueryString: '',
      currentQueryFilter: defaultQueryFilter(),
      selectedEvents: [],
      displayOptions: {
        isCompact: false,
        showTags: true,
        showEmojis: true,
        showMillis: false,
        showTimelineName: true,
      },
      showHistogram: false,
      branchParent: null,
      sortOrderAsc: true,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    highlightEventId() {
      if (this.highlightEvent) {
        return this.highlightEvent._id
      }
      return null
    },
    totalHits() {
      if (this.eventList.meta.es_total_count > 0 && this.eventList.meta.es_total_count_complete === 0) {
        return this.eventList.meta.es_total_count
      }
      return this.eventList.meta.es_total_count_complete || 0
    },
    totalHitsForPagination() {
      // Opensearch has a limit of 10k events when paginating
      return this.eventList.meta.es_total_count || 0
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
    timeFilterChips: function () {
      return this.currentQueryFilter.chips.filter((chip) => chip.type.startsWith('datetime'))
    },
    currentSearchNode() {
      return this.$store.state.currentSearchNode
    },
    headers() {
      let baseHeaders = [
        {
          text: '',
          value: 'data-table-select',
          sortable: false,
        },
        {
          value: 'actions',
          width: '105',
          sortable: false,
        },
        {
          text: 'Datetime (UTC) ',
          align: 'start',
          value: '_source.timestamp',
          width: '200',
          sortable: true,
        },
        {
          value: '_source.comment',
          width: '40',
          sortable: false,
        },
      ]
      let extraHeaders = []
      this.selectedFields.forEach((field) => {
        let header = {
          text: field.field,
          align: 'start',
          value: '_source.' + field.field,
          sortable: false,
        }
        if (field.field === 'message') {
          header.width = '100%'
          extraHeaders.unshift(header)
        } else {
          extraHeaders.push(header)
        }
      })

      // Extend the column headers from position 3 (after the actions column)
      baseHeaders.splice(3, 0, ...extraHeaders)

      // Add timeline name based on configuration
      if (this.displayOptions.showTimelineName) {
        baseHeaders.push({
          value: 'timeline_name',
          align: 'end',
          sortable: false,
        })
      }
      return baseHeaders
    },
  },
  methods: {
    sortEvents(sortAsc) {
      if (sortAsc) {
        this.currentQueryFilter.order = 'asc'
      } else {
        this.currentQueryFilter.order = 'desc'
      }
      this.search(true, true, false)
    },
    getFieldName: function (field) {
      return 'item._source.' + field
    },
    toggleDetailedEvent: function (row) {
      let index = this.expandedRows.findIndex((x) => x._id === row._id)
      if (this.expandedRows.some((event) => event._id === row._id)) {
        if (row.showDetails) {
          row['showDetails'] = false
          this.expandedRows.splice(index, 1)
          this.$set(row, 'showComments', false)
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
    newComment: function (row) {
      if (row.showDetails) {
        this.$set(row, 'showComments', true)
      } else {
        this.$set(row, 'showComments', true)
        this.toggleDetailedEvent(row)
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
        timeline = this.sketch.active_timelines.find((timeline) => timeline.searchindex.index_name === event._index)
      } else {
        timeline = this.sketch.active_timelines.find((timeline) => timeline.id === event._source.__ts_timeline_id)
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
    getAllIndices: function () {
      let allIndices = []
      this.sketch.active_timelines.forEach((timeline) => {
        let isLegacy = this.meta.indices_metadata[timeline.searchindex.index_name].is_legacy
        if (isLegacy) {
          allIndices.push(timeline.searchindex.index_name)
        } else {
          allIndices.push(timeline.id)
        }
      })
      return allIndices
    },
    search: function (resetPagination = true, incognito = false, parent = false) {
      // Exit early if there are no indices selected.
      if (this.currentQueryFilter.indices && !this.currentQueryFilter.indices.length) {
        this.eventList = emptyEventList()
        return
      }

      // If all timelines are selected, make sure that the timeline filter is updated so that
      // filters are applied properly.
      if (this.currentQueryFilter.indices[0] === '_all' || this.currentQueryFilter.indices === '_all') {
        this.currentQueryFilter.indices = this.getAllIndices()
      }

      // Exit early if there is no query string or DSL provided.
      if (!this.currentQueryString && !this.currentQueryDsl) {
        return
      }

      this.searchInProgress = true
      this.selectedEvents = []
      this.eventList = emptyEventList()

      if (resetPagination) {
        this.tableOptions.page = 1
        this.currentPage = 1
        this.currentItemsPerPage = this.tableOptions.itemsPerPage
        this.currentQueryFilter.size = this.tableOptions.itemsPerPage
        this.currentQueryFilter.from = 0
      }

      // Update with selected fields
      this.currentQueryFilter.fields = this.selectedFields

      let formData = {}
      if (this.currentQueryDsl) {
        formData.dsl = this.currentQueryDsl
        formData.filter = this.currentQueryFilter
      }

      if (this.currentQueryString) {
        formData.query = this.currentQueryString
        formData.filter = this.currentQueryFilter
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

      ApiClient.search(this.sketch.id, formData)
        .then((response) => {
          this.eventList.objects = response.data.objects
          this.eventList.meta = response.data.meta
          this.searchInProgress = false
          this.$emit('countPerTimeline', response.data.meta.count_per_timeline)
          this.$emit('countPerIndex', response.data.meta.count_per_index)

          this.addTimeBubbles()

          if (!incognito) {
            EventBus.$emit('createBranch', this.eventList.meta.search_node)
            this.$store.dispatch('updateSearchHistory')
            this.branchParent = this.eventList.meta.search_node.id
          }
        })
        .catch((e) => {
          this.errorSnackBar('Sorry, there was a problem fetching your search results. Please try again.')
          console.error(e)
        })
    },
    exportSearchResult: function () {
      let formData = {
        query: this.currentQueryString,
        filter: this.currentQueryFilter,
        file_name: 'export.zip',
      }
      ApiClient.exportSearchResult(this.sketch.id, formData)
        .then((response) => {
          let fileURL = window.URL.createObjectURL(new Blob([response.data]))
          let fileLink = document.createElement('a')
          let fileName = 'export.zip'
          fileLink.href = fileURL
          fileLink.setAttribute('download', fileName)
          document.body.appendChild(fileLink)
          fileLink.click()
        })
        .catch((e) => {
          console.error(e)
        })
    },
    addChip: function (chip) {
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = []
      }
      this.currentQueryFilter.chips.push(chip)
      this.search()
    },
    removeChip: function (chip, search = true) {
      let chipIndex = this.currentQueryFilter.chips.findIndex((c) => c.value === chip.value)
      this.currentQueryFilter.chips.splice(chipIndex, 1)
      if (search) {
        this.search()
      }
    },
    removeChips: function (chips, search = true) {
      if (!Array.isArray(chips)) {
        this.errorSnackBar('Not an array of chips')
        return
      }
      chips.forEach((chip) => {
        this.removeChip(chip, false)
      })
      if (search) {
        this.search()
      }
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
    paginate: function () {
      // Reset pagination if number of pages per page changes.
      if (this.tableOptions.itemsPerPage !== this.currentItemsPerPage) {
        this.tableOptions.page = 1
        this.currentPage = 1
        this.currentItemsPerPage = this.tableOptions.itemsPerPage
        this.currentQueryFilter.size = this.tableOptions.itemsPerPage
        this.search(true, true)
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
      this.search(false, true)
    },
    updateSelectedFields: function (value) {
      // If we haven't fetched the field before, do an new search.
      value.forEach((field) => {
        if (!this.headers.filter((e) => e.field === field.field).length > 0) {
          this.search(true, true)
        }
      })
    },
    removeField: function (index) {
      this.selectedFields.splice(index, 1)
    },
    toggleStar(event) {
      if (event._source.label.includes('__ts_star')) {
        event._source.label.splice(event._source.label.indexOf('__ts_star'), 1)
      } else {
        event._source.label.push('__ts_star')
      }
      ApiClient.saveEventAnnotation(this.sketch.id, 'label', '__ts_star', event, this.currentSearchNode)
        .then((response) => {})
        .catch((e) => {
          console.error(e)
        })
    },
    toggleMultipleStars: function () {
      this.selectedEvents.forEach((event) => {
        if (event._source.label.includes('__ts_star')) {
          event._source.label.splice(event._source.label.indexOf('__ts_star'), 1)
        } else {
          event._source.label.push('__ts_star')
        }
      })
      ApiClient.saveEventAnnotation(this.sketch.id, 'label', '__ts_star', this.selectedEvents, this.currentSearchNode)
        .then((response) => {
          this.selectedEvents = []
        })
        .catch((e) => {})
    },
    saveSearch: function () {
      ApiClient.createView(this.sketch.id, this.saveSearchFormName, this.currentQueryString, this.currentQueryFilter)
        .then((response) => {
          this.saveSearchFormName = ''
          this.saveSearchMenu = false
          let newView = response.data.objects[0]
          this.$store.state.meta.views.push(newView)
        })
        .catch((e) => {})
    },
  },
  watch: {
    tableOptions: {
      handler(newVal, oldVal) {
        // Return early if the sort order changed.
        // The search is done in the sortEvents method.
        if (oldVal.sortDesc === undefined) return
        if (newVal.sortDesc[0] !== oldVal.sortDesc[0]) return

        this.paginate()
      },
      deep: true,
    },
    queryRequest: {
      handler(newQueryRequest, oldqueryRequest) {
        // Return early if this isn't a new request.
        if (newQueryRequest === oldqueryRequest || !newQueryRequest) {
          return
        }
        this.currentQueryString = newQueryRequest.queryString || ''
        this.currentQueryFilter = newQueryRequest.queryFilter || defaultQueryFilter()
        this.currentQueryDsl = newQueryRequest.queryDsl || null
        let resetPagination = newQueryRequest['resetPagination'] || false
        let incognito = newQueryRequest['incognito'] || false
        let parent = newQueryRequest['parent'] || false
        // Set additional fields. This is used when loading filter from a saved search.
        if (this.currentQueryFilter.fields) {
          this.selectedFields = this.currentQueryFilter.fields
        }
        // Preserve user defined sort order.
        if (this.sortOrderAsc) {
          this.currentQueryFilter.order = 'asc'
        } else {
          this.currentQueryFilter.order = 'desc'
        }
        this.search(resetPagination, incognito, parent)
      },
      deep: true,
    },
  },
  created() {
    if (Object.keys(this.queryRequest).length) {
      this.currentQueryString = this.queryRequest.queryString
      this.currentQueryFilter = { ...this.queryRequest.queryFilter } || defaultQueryFilter()
      this.currentQueryDsl = { ...this.queryRequest.queryDsl }
      // Set additional fields when loading filter from a saved search.
      if (this.currentQueryFilter.fields) {
        this.selectedFields = this.currentQueryFilter.fields
      }
      this.search()
    }
  },
}
</script>

<style lang="scss">
.ts-event-field-container {
  position: relative;
  max-width: 100%;
  height: 100%;
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
  top: 50%;
  transform: translateY(-50%);
  left: 0;
}

.ts-event-field-highlight {
  font-weight: bold;
  color: red;
}

.v-data-table__expanded.v-data-table__expanded__content {
  box-shadow: none !important;
}

.ts-time-bubble {
  width: 120px;
  height: 25px;
  border-radius: 20px;
  position: relative;
  margin: 0 0 0 136px;
  text-align: center;
  font-size: var(--font-size-small);
}

.ts-time-bubble-text {
  font-size: 0.8em;
  padding-top: 4px;
}

.ts-time-bubble-vertical-line {
  width: 2px;
  height: 15px;
  margin: 0 0 0 194px;
  background-color: #f5f5f5;
}

.datetime-table-cell {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

// Adjust padding for event data table
.v-data-table td,
th {
  padding: 0 10px 0 0 !important;
}

.v-data-table td:last-child,
th:last-child {
  padding: 0 !important;
}

.v-data-table td:first-child,
th:first-child {
  padding: 0 0 0 10px !important;
}
</style>
