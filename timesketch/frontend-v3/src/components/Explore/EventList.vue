<!--
Copyright 2025 Google Inc. All rights reserved.

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
    <v-alert v-model="showBanner" dense dismissible type="info">
      Data may be incomplete. Some timelines are still loading.
    </v-alert>

    <v-dialog v-model="exportDialog" width="700">
      <v-card flat class="pa-5">
        <v-progress-circular
          indeterminate
          size="20"
          width="1"
        ></v-progress-circular>
        <span class="ml-5">Exporting {{ totalHits }} events</span>
      </v-card>
    </v-dialog>

    <div v-if="!eventList.objects.length && !searchInProgress && !currentQueryString">
      <ExploreWelcomeCard></ExploreWelcomeCard>
    </div>

    <div v-if="!eventList.objects.length && !searchInProgress && currentQueryString">
      <SearchNotFoundCard
        :current-query-string="currentQueryString"
        :filter-chips="filterChips"
        :disable-save-search="disableSaveSearch"
        @save-search-clicked="saveSearchMenu = true"
      ></SearchNotFoundCard>
    </div>

    <v-dialog
      v-model="saveSearchMenu"
      v-if="!disableSaveSearch"
      width="500"
    >
      <v-card class="pa-4">
        <h3>Save Search</h3>
        <br />
        <v-text-field
          clearable
          v-model="saveSearchFormName"
          required
          placeholder="Name your saved search"
          outlined
          dense
          autofocus
          @focus="$event.target.select()"
          :rules="saveSearchNameRules"
        >
        </v-text-field>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="saveSearchMenu = false"> Cancel </v-btn>
          <v-btn
            text
            color="primary"
            @click="saveSearch"
            :disabled="
              !saveSearchFormName || saveSearchFormName.length > 255
            "
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- <div v-if="highlightEvent" class="mt-4">
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
    </div> -->

    <!-- <div class="ts-event-list-container">
      <v-card
        v-if="(eventList.objects.length > 0 || searchInProgress) && userSettings.eventSummarization && !eventList.meta.summaryError"
        class="ts-ai-summary-card"
        outlined
      >
        <v-card-title class="ts-ai-summary-card-title">
          <v-btn icon small @click="toggleSummary" class="ts-ai-summary-fold-btn">
            <v-icon>{{ summaryCollapsed ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</v-icon>
          </v-btn>
          <v-icon small color="primary" class="ml-1 mr-2 ts-ai-summary-icon">mdi-shimmer</v-icon>
          <div class="ts-ai-summary-text-group">
            <span class="ts-ai-summary-title">AI Summary</span>
            <span v-if="eventList.objects.length > 0" class="ts-ai-summary-subtitle">
              (for {{ eventList.objects.length }} events in this view)
            </span>
          </div>
          <v-btn icon small class="ml-1 ts-ai-summary-info-btn" :title="summaryInfoMessage">
            <v-icon small>mdi-information-outline</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text v-show="!summaryCollapsed" class="ts-ai-summary-text">
          <div v-if="isSummaryLoading || !eventList.meta.summary">
            <div class="ts-summary-placeholder-line shimmer"></div>
            <div class="ts-summary-placeholder-line shimmer short"></div>
            <div class="ts-summary-placeholder-line shimmer long"></div>
          </div>
          <div v-else v-html="eventList.meta.summary"></div>
        </v-card-text>
      </v-card>
    </div> -->

    <div v-if="eventList.objects.length || searchInProgress">
      <!-- <v-data-table
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
      > -->
      <v-data-table-server
        v-model="selectedEventIds"
        v-model:items-per-page="itemsPerPage"
        :headers="headers"
        :items="eventList.objects"
        :items-per-page-options="[10, 40, 80, 100, 200, 500]"
        items-per-page-text="Rows per page:"
        :show-current-page="true"
        :page="currentPage"
        :loading="searchInProgress"
        :items-length="totalHitsForPagination"
        loading-text="Searching... Please wait"
        show-select
        disable-filtering
        must-sort
        hover
        :sort-desc="sortOrderAsc"
        @update:sort-desc="sortEvents"
        @update:options="paginate"
        @update:items-per-page="itemsPerPageChanged"
        :sort-by="['_source.timestamp']"
        :hide-default-footer="totalHits < 11 || disablePagination"
        :density="displayOptions.isCompact ? 'compact' : 'comfortable'"
        fixed-header
        expanded-row="expandedRows"
        item-value="_id"
        expand-on-click
      >
        <template v-slot:top="{ pagination, options, updateOptions }">
          <v-toolbar dense flat color="transparent">
            <div v-if="!selectedEventIds.length">
              <span style="display: inline-block; min-width: 200px">
                {{ fromEvent }}-{{ toEvent }} of {{ totalHits }} events ({{
                  totalTime
                }}s)
              </span>

              <!-- Save search -->
              <v-btn
                icon="mdi-content-save-outline"
                title="Save current search"
                @click="saveSearchMenu = true"
                v-if="!disableSaveSearch"
              ></v-btn>

              <!-- Histogram -->
              <v-btn
                icon="mdi-chart-bar"
                title="Toggle event histogram"
                @click="showHistogram = !showHistogram"
                v-if="!disableHistogram"
              ></v-btn>

              <!-- Select columns -->
              <v-dialog
                v-model="columnDialog"
                v-if="!disableColumns"
                max-width="500px"
                scrollable
              >
                <template v-slot:activator="{ props }">
                  <v-btn icon v-bind="props">
                    <v-icon title="Modify columns"
                      >mdi-view-column-outline</v-icon
                    >
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
                    <v-btn
                      text
                      @click="
                        selectedFields = [{ field: 'message', type: 'text' }]
                      "
                    >
                      Reset
                    </v-btn>
                    <v-btn text color="primary" @click="columnDialog = false">
                      Set columns
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-dialog>

              <!-- Export search results -->
              <v-btn icon @click="exportSearchResult()">
                <v-icon title="Download current view as CSV"
                  >mdi-download</v-icon
                >
              </v-btn>

              <v-menu
                v-if="!disableSettings"
                offset-y
                :close-on-content-click="false"
              >
                <template v-slot:activator="{ props }">
                  <v-btn icon v-bind="props">
                    <v-icon title="View settings">mdi-dots-horizontal</v-icon>
                  </v-btn>
                </template>
                <v-card outlined width="300">
                  <v-list>
                    <v-list-subheader>Density</v-list-subheader>
                    <v-list-item>
                      <v-radio-group
                        v-model="displayOptions.isCompact"
                        color="primary"
                      >
                        <v-radio label="Comfortable" :value="false"></v-radio>
                        <v-radio label="Compact" :value="true"></v-radio>
                      </v-radio-group>
                    </v-list-item>
                    <v-divider></v-divider>
                    <v-list-subheader>Misc</v-list-subheader>
                    <v-list-item>
                      <v-switch
                        hide-details
                        label="Show tags"
                        color="primary"
                        v-model="displayOptions.showTags"
                      ></v-switch>
                      <v-switch
                        hide-details
                        label="Show emojis"
                        color="primary"
                        v-model="displayOptions.showEmojis"
                      ></v-switch>
                      <v-switch
                        hide-details
                        label="Show timeline name"
                        color="primary"
                        v-model="displayOptions.showTimelineName"
                      ></v-switch>
                    </v-list-item>
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

                <v-menu v-model="showEventTagMenu" offset-x :close-on-content-click="false">
                  <template v-slot:activator="{ props }">
                    <v-btn x-small outlined v-bind="props">
                      <v-icon left>mdi-tag-plus-outline</v-icon>
                      Modify Tags
                    </v-btn>
                  </template>

                  <ts-event-tag-dialog :events="selectedEvents" @close="showEventTagMenu = false"></ts-event-tag-dialog>

                </v-menu>
            </div>

            <v-spacer></v-spacer>

            <v-data-table-footer
              v-if="totalHits > 11 && !disablePagination"
              :pagination="pagination"
              :options="options"
              @update:options="updateOptions"
              :show-current-page="true"
              :items-per-page-options="[10, 40, 80, 100, 200, 500]"
              items-per-page-text="Rows per page:"
            ></v-data-table-footer>
          </v-toolbar>

          <v-card v-if="showHistogram" outlined class="my-3">
            <v-toolbar dense flat color="transparent">
              <v-spacer></v-spacer>
              <v-btn
                v-if="timeFilterChips.length"
                text
                color="primary"
                @click="removeChips(timeFilterChips)"
              >
                reset
              </v-btn>
              <v-btn icon @click="showHistogram = false">
                <v-icon title="Close histogram">mdi-close</v-icon>
              </v-btn>
            </v-toolbar>
            <ts-bar-chart
                :chart-data="eventList.meta.count_over_time"
                @addChip="addChipFromHistogram($event)"
              ></ts-bar-chart>
          </v-card>
        </template>

        <!-- Event details -->
        <template v-slot:expanded-row="{ columns, item }">
          <td :colspan="columns.length">
            <!-- Details -->
            <!-- <v-container v-if="item.showDetails" fluid class="mt-4"> -->
            <v-container fluid class="mt-4">
              <ts-event-detail :event="item"></ts-event-detail>
            </v-container>

            <!-- Time bubble -->
            <v-divider v-if="item.showDetails && item.deltaDays"></v-divider>
            <div v-if="item.deltaDays > 0" class="ml-7">
              <div
                class="ts-time-bubble-vertical-line ts-time-bubble-vertical-line-color"
                v-bind:style="getTimeBubbleColor(item)"
              ></div>
              <div
                class="ts-time-bubble ts-time-bubble-color"
                v-bind:style="getTimeBubbleColor(item)"
              >
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
          <v-icon
            v-if="item._source.label.includes('__ts_star')"
            title="Toggle star status"
            @click.stop="toggleStar(item)"
            color="amber"
            >mdi-star</v-icon
          >
          <v-icon v-else title="Toggle star status" @click.stop="toggleStar(item)"
            >mdi-star-outline</v-icon
          >

          <!-- Tag menu -->
          <span class="ml-1">
            <ts-event-tag-menu :event="item"></ts-event-tag-menu>
          </span>

          <!-- Action sub-menu -->
          <span class="ml-1">
            <ts-event-action-menu :event="item"></ts-event-action-menu>
          </span>
        </template>

        <!-- Datetime field with action buttons -->
        <template v-slot:item._source.timestamp="{ item }">
          <div
            v-bind:style="getTimelineColor(item)"
            class="datetime-table-cell"
          >
            {{
              $filters.toISO8601(
                $filters.formatTimestamp(item._source.timestamp)
              )
            }}
          </div>
        </template>

        <!-- Generic slot for any field type. Adds tags and emojis to the first column. -->
        <template
          v-for="(field, index) in headers"
          v-slot:[getFieldName(field.title)]="{ item }"
        >
          <div
            :key="field.title"
            class="ts-event-field-container"
            style="cursor: pointer"
            @click="toggleDetailedEvent(item)"
          >
            <span
              :class="{
                'ts-event-field-ellipsis': field.title === 'message',
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
                <ts-event-tags
                  :item="item"
                  :tagConfig="tagConfig"
                  :showDetails="item.showDetails"
                ></ts-event-tags>
              </span>
              <!-- Emojis -->
              <span v-if="displayOptions.showEmojis && index === 3">
                <span
                  class="mr-2"
                  v-for="emoji in item._source.__ts_emojis"
                  :key="emoji"
                  v-html="emoji + ';'"
                  :title="meta.emojis[emoji]"
                >
                </span>
              </span>
              <span>{{ item._source[field.title] }}</span>
            </span>
          </div>
        </template>

        <!-- Timeline name field -->
        <template v-slot:item.timeline_name="{ item }">
          <v-chip
            label
            style="margin-top: 1px; margin-bottom: 1px; font-size: 0.8em"
          >
            <span
              class="timeline-name-ellipsis"
              style="width: 130px; text-align: center"
              >{{ getTimeline(item).name }}</span
            ></v-chip
          >
        </template>

        <!-- Comment field -->
        <template v-slot:item._source.comment="{ item }">
          <div class="d-inline-block">
            <v-btn
              icon
              small
              @click="toggleDetailedEvent(item)"
              v-if="item._source.comment.length"
            >
              <v-badge
                :offset-y="10"
                :offset-x="10"
                bordered
                :content="item._source.comment.length"
              >
                <v-icon
                  :title="
                    item['showDetails']
                      ? 'Close event &amp; comments'
                      : 'Open event &amp; comments'
                  "
                  small
                >
                  mdi-comment-text-multiple-outline
                </v-icon>
              </v-badge>
            </v-btn>
          </div>

          <div
            v-if="
              item['showDetails'] &&
              !item._source.comment.length &&
              !item.showComments
            "
            class="d-inline-block"
          >
            <v-btn icon small @click="newComment(item)">
              <v-icon title="Add a comment"> mdi-comment-plus-outline </v-icon>
            </v-btn>
          </div>

          <div
            v-if="
              item['showDetails'] &&
              !item._source.comment.length &&
              item.showComments
            "
            class="d-inline-block"
          >
            <v-btn icon small @click="item.showComments = false">
              <v-icon title="Close comments">
                mdi-comment-remove-outline
              </v-icon>
            </v-btn>
          </div>
        </template>
      </v-data-table-server>
    </div>
  </div>
</template>

<script>
import ApiClient from "@/utils/RestApiClient.js";
import EventBus from "@/event-bus.js";
import { useAppStore } from "@/stores/app";

import TsBarChart from './BarChart.vue'
import TsEventDetail from "./EventDetail.vue";
import TsEventTagMenu from "./EventTagMenu.vue";
import TsEventTags from "./EventTags.vue";
import TsEventActionMenu from "./EventActionMenu.vue";
import TsEventTagDialog from "./EventTagDialog.vue";

const defaultQueryFilter = () => {
  return {
    from: 0,
    terminate_after: 40,
    size: 40,
    indices: ["_all"],
    order: "asc",
    chips: [],
  };
};

const emptyEventList = () => {
  return {
    meta: {
      count_per_index: {},
      count_per_timeline: {},
    },
    objects: [],
  };
};

export default {
  components: {
    // TsBarChart,
    TsEventDetail,
    TsEventTagMenu,
    TsEventTags,
    TsEventActionMenu,
    TsBarChart,
    TsEventTagDialog,
  },
  props: {
    queryRequest: {
      type: Object,
      default: () => {},
    },
    // itemsPerPage: {
    //   type: Number,
    //   default: 40,
    // },
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
      showEventTagMenu: false,
      appStore: useAppStore(),
      columnHeaders: [
        {
          title: "",
          value: "field",
        },
      ],
      isSummaryLoading: false,
      itemsPerPage: 40,
      expandedRows: [],
      selectedFields: [{ field: "message", type: "text" }],
      searchColumns: "",
      columnDialog: false,
      saveSearchMenu: false,
      saveSearchFormName: "",
      saveSearchNameRules: [
        (v) => !!v || "Name is required.",
        (v) => (v && v.length <= 255) || "Name is too long.",
      ],
      selectedEventTags: [],
      tagConfig: {
        good: { color: "success", label: "mdi-check-circle-outline" },
        bad: { color: "red", label: "mdi-alert-circle-outline" },
        suspicious: { color: "warning", label: "mdi-help-circle-outline" },
      },
      searchInProgress: false,
      exportDialog: false,
      currentPage: 1,
      eventList: {
        meta: {},
        objects: [],
      },
      currentQueryString: "",
      currentQueryFilter: defaultQueryFilter(),
      selectedEventIds: [],
      displayOptions: {
        isCompact: false,
        showTags: true,
        showEmojis: true,
        showTimelineName: true,
      },
      showHistogram: false,
      branchParent: null,
      sortOrderAsc: true,
      summaryCollapsed: false,
      showBanner: false,
    };
  },
  computed: {
    summaryInfoMessage() {
      const totalEvents = this.eventList.meta.summary_event_count;
      const uniqueEvents = this.eventList.meta.summary_unique_event_count;
      return `[experimental] This summary is based on the message field on your current page (${totalEvents} rows, ${uniqueEvents} unique message fields).`;
    },
    selectedEvents() {
      return this.selectedEventIds.map(id => {
        return this.eventList.objects.find(o => o._id === id);
      });
    },
    sketch() {
      return this.appStore.sketch;
    },
    meta() {
      return this.appStore.meta;
    },
    highlightEventId() {
      if (this.highlightEvent) {
        return this.highlightEvent._id;
      }
      return null;
    },
    totalHits() {
      if (
        this.eventList.meta.es_total_count > 0 &&
        this.eventList.meta.es_total_count_complete === 0
      ) {
        return this.eventList.meta.es_total_count;
      }
      return this.eventList.meta.es_total_count_complete || 0;
    },
    totalHitsForPagination() {
      // Opensearch has a limit of 10k events when paginating
      // TODO jbn: Figure this out
      return 10000;
      //return this.eventList.meta.es_total_count || 0
    },
    totalTime() {
      return this.eventList.meta.es_time / 1000 || 0;
    },
    fromEvent() {
      return this.currentQueryFilter.from || 1;
    },
    toEvent() {
      if (this.totalHits < this.currentQueryFilter.size) {
        return;
      }
      return (
        parseInt(this.currentQueryFilter.from) +
        parseInt(this.currentQueryFilter.size)
      );
    },
    timeFilterChips: function () {
      return this.currentQueryFilter.chips.filter((chip) =>
        chip.type.startsWith("datetime")
      );
    },
    currentSearchNode() {
      return this.appStore.currentSearchNode;
    },
    userSettings() {
      return this.appStore.settings;
    },
    headers() {
      let baseHeaders = [
        {
          key: "data-table-select",
          sortable: false,
        },
        {
          key: "actions",
          width: "90px",
          sortable: false,
        },
        {
          key: "_source.timestamp",
          title: "Datetime (UTC)",
          align: "start",
          width: "200px",
          sortable: true,
        },
        {
          key: "_source.comment",
          width: "40px",
          sortable: false,
        },
      ];
      let extraHeaders = [];
      this.selectedFields.forEach((field) => {
        let header = {
          key: "_source." + field.field,
          title: field.field,
          align: "start",
          sortable: false,
        };
        if (field.field === "message") {
          //header.width = '100vh'
          extraHeaders.unshift(header);
        } else {
          extraHeaders.push(header);
        }
      });

      // Extend the column headers from position 3 (after the actions column)
      baseHeaders.splice(3, 0, ...extraHeaders);

      // Add timeline name based on configuration
      if (this.displayOptions.showTimelineName) {
        baseHeaders.push({
          key: "timeline_name",
          align: "end",
          sortable: false,
          width: "1px", // trick to make the message column expand
        });
      }
      return baseHeaders;
    },
    activeContext() {
      return this.appStore.activeContext;
    },
    settings() {
      return this.appStore.settings;
    },
    filterChips: function () {
      return this.currentQueryFilter.chips.filter(
        (chip) => chip.type === "label" || chip.type === "term"
      );
    },
  },
  methods: {
    toggleSummary() {
      this.summaryCollapsed = !this.summaryCollapsed;
      localStorage.setItem("aiSummaryCollapsed", String(this.summaryCollapsed));
    },
    sortEvents(sortAsc) {
      if (sortAsc) {
        this.currentQueryFilter.order = "asc";
      } else {
        this.currentQueryFilter.order = "desc";
      }
      this.search(true, true, false);
    },
    getFieldName: function (field) {
      return "item._source." + field;
    },
    toggleDetailedEvent: function (row) {
      return;
      let index = this.expandedRows.findIndex((x) => x._id === row._id);
      if (this.expandedRows.some((event) => event._id === row._id)) {
        if (row.showDetails) {
          row["showDetails"] = false;
          this.expandedRows.splice(index, 1);
          //this.$set(row, 'showComments', false)
          row.showComments = false;
        } else {
          row["showDetails"] = true;
          this.expandedRows.splice(index, 1);
          this.expandedRows.push(row);
          return;
        }

        if (row.deltaDays) {
          this.expandedRows.splice(index, 1);
          this.expandedRows.push(row);
        }
      } else {
        row["showDetails"] = true;
        this.expandedRows.push(row);
      }
    },
    newComment: function (row) {
      if (row.showDetails) {
        this.$set(row, "showComments", true);
      } else {
        this.$set(row, "showComments", true);
        this.toggleDetailedEvent(row);
      }
    },
    addTimeBubbles: function () {
      this.expandedRows = [];
      this.eventList.objects.forEach((event, index) => {
        if (index < 1) {
          return;
        }
        let prevEvent = this.eventList.objects[index - 1];
        let timestampMillis = this.$filters.formatTimestamp(
          event._source.timestamp
        );
        let prevTimestampMillis = this.$filters.formatTimestamp(
          prevEvent._source.timestamp
        );
        let timestamp = Math.floor(timestampMillis / 1000);
        let prevTimestamp = Math.floor(prevTimestampMillis / 1000);
        let delta = Math.floor(timestamp - prevTimestamp);
        if (this.order === "desc") {
          delta = Math.floor(prevTimestamp - timestamp);
        }
        let deltaDays = Math.floor(delta / 60 / 60 / 24);
        if (deltaDays > 0) {
          prevEvent["deltaDays"] = deltaDays;
          this.expandedRows.push(prevEvent);
        }
      });
    },
    getTimeline: function (event) {
      let isLegacy = this.meta.indices_metadata[event._index].is_legacy;
      let timeline;
      if (isLegacy) {
        timeline = this.sketch.active_timelines.find(
          (timeline) => timeline.searchindex.index_name === event._index
        );
      } else {
        timeline = this.sketch.active_timelines.find(
          (timeline) => timeline.id === event._source.__ts_timeline_id
        );
      }
      return timeline;
    },
    getTimelineColor(event) {
      let timeline = this.getTimeline(event);
      let backgroundColor = timeline.color;
      if (!backgroundColor.startsWith("#")) {
        backgroundColor = "#" + backgroundColor;
      }
      if (this.$vuetify.theme.dark) {
        return {
          "background-color": backgroundColor,
          filter: "grayscale(25%)",
          color: "#333",
        };
      }
      return {
        "background-color": backgroundColor,
      };
    },
    getTimeBubbleColor() {
      let backgroundColor = "#f5f5f5";
      if (this.$vuetify.theme.dark) {
        backgroundColor = "#333";
      }
      return {
        "background-color": backgroundColor,
      };
    },
    getAllIndices: function () {
      let allIndices = [];
      this.sketch.active_timelines.forEach((timeline) => {
        let isLegacy =
          this.meta.indices_metadata[timeline.searchindex.index_name].is_legacy;
        if (isLegacy) {
          allIndices.push(timeline.searchindex.index_name);
        } else {
          allIndices.push(timeline.id);
        }
      });
      return allIndices;
    },
    search: function (
      resetPagination = true,
      incognito = false,
      parent = false
    ) {
      this.isSummaryLoading = true;

      // Exit early if there are no indices selected.
      if (
        this.currentQueryFilter.indices &&
        !this.currentQueryFilter.indices.length
      ) {
        this.eventList = emptyEventList();
        this.isSummaryLoading = false;
        return;
      }

      // If all timelines are selected, make sure that the timeline filter is updated so that
      // filters are applied properly.
      if (
        this.currentQueryFilter.indices[0] === "_all" ||
        this.currentQueryFilter.indices === "_all"
      ) {
        this.currentQueryFilter.indices = this.getAllIndices();
      }

      // Exit early if there is no query string or DSL provided.
      if (!this.currentQueryString && !this.currentQueryDsl) {
        return;
      }

      this.searchInProgress = true;
      this.selectedEventIds = [];
      this.eventList = emptyEventList();

      if (resetPagination) {
        this.currentPage = 1;
        this.currentQueryFilter.size = this.itemsPerPage;
        this.currentQueryFilter.from = 0;
      }

      // Update with selected fields
      this.currentQueryFilter.fields = this.selectedFields;

      let formData = {};
      if (this.currentQueryDsl) {
        formData.dsl = this.currentQueryDsl;
        formData.filter = this.currentQueryFilter;
      }

      if (this.currentQueryString) {
        formData.query = this.currentQueryString;
        formData.filter = this.currentQueryFilter;
      }

      // Search history
      if (incognito) {
        formData["incognito"] = true;
      }

      if (parent) {
        formData["parent"] = parent;
      }

      if (parent && incognito) {
        this.branchParent = parent;
      }

      if (this.branchParent) {
        formData["parent"] = this.branchParent;
      }

      // Get DFIQ context
      formData["scenario"] = this.activeContext.scenarioId;
      formData["facet"] = this.activeContext.facetId;
      formData["question"] = this.activeContext.questionId;

      formData["include_processing_timelines"] =
        this.settings.showProcessingTimelineEvents;

      ApiClient.search(this.sketch.id, formData)
        .then((response) => {
          this.eventList.objects = response.data.objects;
          this.eventList.meta = response.data.meta;
          this.updateShowBanner();
          this.searchInProgress = false;
          EventBus.$emit(
            "updateCountPerTimeline",
            response.data.meta.count_per_timeline
          );
          this.$emit("countPerTimeline", response.data.meta.count_per_timeline);
          this.$emit("countPerIndex", response.data.meta.count_per_index);

          this.addTimeBubbles();

          if (!incognito) {
            EventBus.$emit("createBranch", this.eventList.meta.search_node);
            this.appStore.updateSearchHistory();
            this.branchParent = this.eventList.meta.search_node.id;
          }
          if (
            this.userSettings.eventSummarization &&
            this.eventList.objects.length > 0
          ) {
            this.fetchEventSummary();
          }
        })
        .catch((e) => {
          console.log("Error fetching search results:", e);
          let msg =
            'Sorry, there was a problem fetching your search results. Error: "' +
            e.response.data.message +
            '"';
          if (
            e.response.data.message.includes("too_many_nested_clauses") ||
            e.response.data.message.includes("query_shard_exception")
          ) {
            msg =
              'Sorry, your query is too complex. Use field-specific search (like "message:(<query terms>)") and try again.';
            this.warningSnackBar(msg);
          } else {
            this.errorSnackBar(msg);
          }
          console.error("Error message: " + msg);
          console.error(e);
        });
    },
    fetchEventSummary: function () {
      const formData = {
        query: this.currentQueryString,
        filter: this.currentQueryFilter,
      };
      ApiClient.llmRequest(this.sketch.id, "llm_summarize", formData)
        .then((response) => {
          this.$set(this.eventList.meta, "summary", response.data.response);
          this.$set(
            this.eventList.meta,
            "summary_event_count",
            response.data.summary_event_count
          );
          this.$set(
            this.eventList.meta,
            "summary_unique_event_count",
            response.data.summary_unique_event_count
          );
          this.isSummaryLoading = false;
        })
        .catch((error) => {
          console.error("Error fetching event summary:", error);
          this.$set(this.eventList.meta, "summaryError", true);
          this.isSummaryLoading = false;
        });
    },
    exportSearchResult: function () {
      this.exportDialog = true;
      const now = new Date();
      const exportFileName = "timesketch_export_" + now.toISOString() + ".zip";
      let formData = {
        query: this.currentQueryString,
        filter: this.currentQueryFilter,
        file_name: exportFileName,
      };
      ApiClient.exportSearchResult(this.sketch.id, formData)
        .then((response) => {
          let fileURL = window.URL.createObjectURL(new Blob([response.data]));
          let fileLink = document.createElement("a");
          fileLink.href = fileURL;
          fileLink.setAttribute("download", exportFileName);
          document.body.appendChild(fileLink);
          fileLink.click();
          this.exportDialog = false;
        })
        .catch((e) => {
          console.error(e);
          this.exportDialog = false;
        });
    },
    addChip: function (chip) {
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = [];
      }
      this.currentQueryFilter.chips.push(chip);
      this.search();
    },
    removeChip: function (chip, search = true) {
      let chipIndex = this.currentQueryFilter.chips.findIndex(
        (c) => c.value === chip.value
      );
      this.currentQueryFilter.chips.splice(chipIndex, 1);
      if (search) {
        this.search();
      }
    },
    removeChips: function (chips, search = true) {
      if (!Array.isArray(chips)) {
        this.errorSnackBar("Not an array of chips");
        return;
      }
      chips.forEach((chip) => {
        this.removeChip(chip, false);
      });
      if (search) {
        this.search();
      }
    },
    addChipFromHistogram: function (chip) {
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = [];
      }
      this.currentQueryFilter.chips.forEach((chip) => {
        if (chip.type === "datetime_range") {
          this.removeChip(chip, false);
        }
      });
      this.addChip(chip);
    },
    itemsPerPageChanged: function (itemsPerPage) {
      // Search with reset pagination set.
      this.search(true, true);
    },
    paginate: function (options) {
      // To avoid double search request exit early if this is the first search for this
      // search session.
      if (this.currentPage === options.page) {
        return;
      }

      this.currentQueryFilter.from =
        options.page * this.currentQueryFilter.size -
        this.currentQueryFilter.size;
      this.currentPage = options.page;
      this.search(false, true);
    },
    updateSelectedFields: function (value) {
      // If we haven't fetched the field before, do an new search.
      value.forEach((field) => {
        if (!this.headers.filter((e) => e.field === field.field).length > 0) {
          this.search(true, true);
        }
      });
    },
    removeField: function (index) {
      this.selectedFields.splice(index, 1);
    },
    toggleStar(event) {
      let count = 0;
      if (event._source.label.includes("__ts_star")) {
        event._source.label.splice(event._source.label.indexOf("__ts_star"), 1);
        count = -1;
      } else {
        event._source.label.push("__ts_star");
        count = 1;
      }
      console.log("Star count: ", count, this.sketch.id, this.currentSearchNode);
      ApiClient.saveEventAnnotation(
        this.sketch.id,
        "label",
        "__ts_star",
        event,
        this.currentSearchNode
      )
        .then((response) => {
          this.appStore.updateEventLabels({ label: "__ts_star", num: count });
        })
        .catch((e) => {
          console.error(e);
        });
    },
    toggleMultipleStars: function () {
      let netStarCountChange = 0;
      this.selectedEvents.forEach((event) => {
        if (event._source.label.includes("__ts_star")) {
          event._source.label.splice(
            event._source.label.indexOf("__ts_star"),
            1
          );
          netStarCountChange--;
        } else {
          event._source.label.push("__ts_star");
          netStarCountChange++;
        }
      });
      ApiClient.saveEventAnnotation(
        this.sketch.id,
        "label",
        "__ts_star",
        this.selectedEvents,
        this.currentSearchNode
      )
        .then((response) => {
          this.appStore.updateEventLabels({
            label: "__ts_star",
            num: netStarCountChange,
          });
          this.selectedEventIds = [];
        })
        .catch((e) => {});
    },
    saveSearch: function () {
      ApiClient.createView(
        this.sketch.id,
        this.saveSearchFormName,
        this.currentQueryString,
        this.currentQueryFilter
      )
        .then((response) => {
          this.saveSearchFormName = "";
          this.saveSearchMenu = false;
          let newView = response.data.objects[0];
          this.appStore.meta.views.push(newView);
        })
        .catch((e) => {});
    },
    updateShowBanner: function () {
      // Show banner only when processing timelines are enabled and at
      // least one enabled timeline is the "processing" state.
      this.showBanner =
        !!this.settings.showProcessingTimelineEvents &&
        this.sketch.active_timelines
          .filter((tl) => this.appStore.enabledTimelines.includes(tl.id))
          .some((tl) => tl.status && tl.status[0].status === "processing");
    },
  },
  watch: {
    queryRequest: {
      handler(newQueryRequest, oldqueryRequest) {
        // Return early if this isn't a new request.
        if (newQueryRequest === oldqueryRequest || !newQueryRequest) {
          return;
        }
        this.currentQueryString = newQueryRequest.queryString || "";
        this.currentQueryFilter =
          newQueryRequest.queryFilter || defaultQueryFilter();
        this.currentQueryDsl = newQueryRequest.queryDsl || null;
        let resetPagination = newQueryRequest["resetPagination"] || false;
        let incognito = newQueryRequest["incognito"] || false;
        let parent = newQueryRequest["parent"] || false;
        // Set additional fields. This is used when loading filter from a saved search.
        if (this.currentQueryFilter.fields) {
          this.selectedFields = this.currentQueryFilter.fields;
        }
        // Preserve user defined sort order.
        if (this.sortOrderAsc) {
          this.currentQueryFilter.order = "asc";
        } else {
          this.currentQueryFilter.order = "desc";
        }
        this.search(resetPagination, incognito, parent);
      },
      deep: true,
    },
    "settings.showProcessingTimelineEvents": {
      handler() {
        this.updateShowBanner();
      },
    },
  },
  created() {
    if (Object.keys(this.queryRequest).length) {
      this.currentQueryString = this.queryRequest.queryString;
      this.currentQueryFilter =
        { ...this.queryRequest.queryFilter } || defaultQueryFilter();
      this.currentQueryDsl = { ...this.queryRequest.queryDsl };
      // Set additional fields when loading filter from a saved search.
      if (this.currentQueryFilter.fields) {
        this.selectedFields = this.currentQueryFilter.fields;
      }
      const storedState = localStorage.getItem("aiSummaryCollapsed");
      if (storedState === "true") {
        this.summaryCollapsed = true;
      }
      this.search();
    }
  },
};
</script>

<style lang="scss">
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

.ts-ai-summary-card {
  border: 1px solid transparent !important;
  border-radius: 8px;
  background-color: #fafafa;
  background-image: linear-gradient(white, white),
    linear-gradient(
      90deg,
      #8ab4f8 0%,
      #81c995 20%,
      #f8c665 40%,
      #ec7764 60%,
      #b39ddb 80%,
      #8ab4f8 100%
    );
  background-origin: border-box;
  background-clip: content-box, border-box;
  background-size: 300% 100%;
  animation: borderBeamIridescent-subtle 6s linear infinite;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.08);
  display: block;
  margin-bottom: 20px;
}

.v-data-table {
  display: block; /* Ensure block display for data table */
}

@keyframes borderBeamIridescent-subtle {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 100% 50%;
  }
}

.theme--dark.ts-ai-summary-card {
  background-color: #1e1e1e;
  border-color: hsla(0, 0%, 100%, 0.12) !important;
  background-image: linear-gradient(#1e1e1e, #1e1e1e),
    linear-gradient(
      90deg,
      #8ab4f8 0%,
      #81c995 20%,
      #f8c665 40%,
      #ec7764 60%,
      #b39ddb 80%,
      #8ab4f8 100%
    );
  box-shadow: 0 2px 5px rgba(255, 255, 255, 0.08);
  display: block;
  margin-bottom: 20px;
}

.ts-ai-summary-text {
  white-space: pre-line;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  margin-top: -10px;
  padding-left: 10px;
  padding-right: 10px;
}

.ts-ai-summary-card .v-btn--icon {
  cursor: pointer;
}

.ts-ai-summary-card .v-btn--icon:hover {
  opacity: 0.8;
}

.ts-summary-placeholder-line {
  height: 1em;
  background-color: #e0e0e0;
  margin-bottom: 0.5em;
  border-radius: 4px;
  width: 100%;
}

.ts-summary-placeholder-line.short {
  width: 60%;
}

.ts-summary-placeholder-line.long {
  width: 80%;
}

.shimmer {
  background: linear-gradient(to right, #e0e0e0 8%, #f0f0f0 18%, #e0e0e0 33%);
  background-size: 800px 100%;
  animation: shimmer-animation 1.5s infinite linear forwards;
}

@keyframes shimmer-animation {
  0% {
    background-position: -468px 0;
  }
  100% {
    background-position: 468px 0;
  }
}

.ts-event-list-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 20px;
}

::v-deep .no-transition {
  transition: none !important;
}

.ts-ai-summary-card-title {
  display: flex;
  align-items: baseline;
}

.ts-ai-summary-title {
  margin-right: 8px;
  font-weight: normal;
}

.ts-ai-summary-subtitle {
  font-size: 0.7em;
  color: grey;
  vertical-align: middle;
  display: inline-block;
}
</style>
