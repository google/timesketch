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
    <!-- Right side menu -->
    <!-- Placeholder at the moment. Keeping it here for quick development later. -->

    <!-- Search and Filters -->
    <v-card flat class="pa-3 pt-0 mt-n3" color="transparent">
      <v-card class="d-flex align-start mb-1" outlined>
        <!-- The search-mode selector doubles as the query-language selector:
             PPL and SQL appear alongside Query String and Wildcard on a
             cluster that can serve them. -->
        <ts-search-mode-toggle
          v-model="selectedSearchType"
          :direct-query-enabled="directQueryEnabled"
        ></ts-search-mode-toggle>
        <v-sheet v-if="isLucene" class="mt-2">
          <ts-search-history-buttons @toggleSearchHistory="toggleSearchHistory()"></ts-search-history-buttons>
        </v-sheet>

        <v-menu
          v-if="isLucene"
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
              flat
              solo
              class="pa-2"
              id="tsSearchInput"
              autocomplete="off"
              @keyup.enter="search()"
              @click="showSearchDropdown = true"
              ref="searchInput"
              v-bind="attrs"
              v-on="on"
            >
              <template v-slot:append>
                <v-icon title="Run search" @click="search()" class="mr-3">mdi-magnify</v-icon>
                <v-icon title="Show search examples" @click="showSearchHelp = true">mdi-help-circle-outline</v-icon>
              </template>
            </v-text-field>
          </template>

          <ts-search-dropdown
            v-click-outside="onClickOutside"
            :selected-labels="selectedLabels"
            :query-string="currentQueryString"
            :search-mode="searchMode"
            @setActiveView="searchView"
            @addChip="addChip"
            @updateLabelChips="updateLabelChips()"
            @close-on-click="showSearchDropdown = false"
            @node-click="jumpInHistory"
            @setQueryAndFilter="setQueryAndFilter"
          >
          </ts-search-dropdown>
        </v-menu>

        <!-- PPL and SQL are written as multi-line pipelines and statements, so
             they get a monospace auto-growing editor rather than the Lucene
             one-liner. Enter inserts a newline; the run shortcut submits. -->
        <ts-direct-query-editor
          v-else
          v-model="currentQueryString"
          :language="queryLanguage"
          :running="directQueryLoading"
          :timeline-count="enabledTimelines.length"
          :start-time="directQueryTimeRange.start"
          :end-time="directQueryTimeRange.end"
          @update:timeRange="directQueryTimeRange = $event"
          @run="search()"
          @cancel="cancelDirectQuery()"
          @explain="explainDirectQuery()"
          @help="showSearchHelp = true"
        ></ts-direct-query-editor>
      </v-card>

      <!-- Search History -->
      <div class="mt-4">
        <v-card v-show="showSearchHistory && isLucene" outlined>
          <v-toolbar dense flat>
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
              <v-icon title="Close search history">mdi-close</v-icon>
            </v-btn>
          </v-toolbar>

          <v-divider></v-divider>

          <div
            v-dragscroll
            class="pa-md-4 no-scrollbars"
            style="overflow: scroll; white-space: nowrap; max-height: 500px; min-height: 100px"
          >
            <ts-search-history-tree
              @node-click="jumpInHistory"
              :show-history="showSearchHistory"
              v-bind:style="{ transform: 'scale(' + zoomLevel + ')' }"
              style="transform-origin: top left"
            ></ts-search-history-tree>
          </div>
        </v-card>
      </div>

      <!-- Search Help Dialog -->
      <v-dialog v-model="showSearchHelp" max-width="1800" scrollable>
        <ts-search-help-card :flat="true" :query-language="queryLanguage" @close-dialog="showSearchHelp = false"></ts-search-help-card>
      </v-dialog>


      <!-- Timeline picker -->
      <div>
        <v-toolbar flat dense style="background-color: transparent" class="mt-n3">
          <v-btn small icon @click="showTimelines = !showTimelines">
            <v-icon v-if="showTimelines" title="Hide Timelines">mdi-chevron-up</v-icon>
            <v-icon v-else title="Show Timelines">mdi-chevron-down</v-icon>
          </v-btn>
          <span class="timeline-header">
            <ts-upload-timeline-form-button btn-type="small"></ts-upload-timeline-form-button>
            <v-dialog v-model="addManualEvent" width="600">
              <template v-slot:activator="{ on, attrs }">
                <v-btn small text rounded color="primary" v-bind="attrs" v-on="on">
                  <v-icon left small> mdi-plus </v-icon>
                  Add manual event
                </v-btn>
              </template>
              <ts-add-manual-event
                app
                @cancel="addManualEvent = false"
                :datetimeProp="datetimeManualEvent"
              ></ts-add-manual-event>
            </v-dialog>
            <v-btn small text rounded color="primary" @click.stop="enableAllTimelines()">
              <v-icon left small>mdi-eye</v-icon>
              <span>Select all</span>
            </v-btn>
            <v-btn small text rounded color="primary" @click.stop="disableAllTimelines()">
              <v-icon left small>mdi-eye-off</v-icon>
              <span>Unselect all</span>
            </v-btn>
          </span>
        </v-toolbar>
        <v-expand-transition>
          <div v-show="showTimelines">
            <ts-timeline-picker
              :current-query-filter="currentQueryFilter"
              :count-per-index="countPerIndex"
              :count-per-timeline="countPerTimeline"
            ></ts-timeline-picker>
          </div>
        </v-expand-transition>
      </div>

      <!-- Time filter chips -->
      <div v-if="isLucene">
        <span v-for="(chip, index) in timeFilterChips" :key="index + chip.value">
          <v-menu offset-y content-class="menu-with-gap">
            <template v-slot:activator="{ on }">
              <v-chip outlined v-on="on">
                <v-icon left small> mdi-clock-outline </v-icon>
                <span v-bind:style="[!chip.active ? { 'text-decoration': 'line-through', opacity: '50%' } : '']">
                  <span>{{ chip.value.split(',')[0] }}</span>
                  <span v-if="chip.type === 'datetime_range' && chip.value.split(',')[0] !== chip.value.split(',')[1]">
                    &rarr; {{ chip.value.split(',')[1] }}</span
                  >
                </span>
              </v-chip>
            </template>
            <v-card>
              <v-list>
                <!-- Edit timefilter menu -->
                <v-menu
                  offset-y
                  :close-on-content-click="false"
                  :close-on-click="true"
                  nudge-top="70"
                  content-class="menu-with-gap"
                  allow-overflow
                  style="overflow: visible"
                >
                  <template v-slot:activator="{ on, attrs }">
                    <v-list-item v-bind="attrs" v-on="on">
                      <v-list-item-action>
                        <v-icon>mdi-square-edit-outline</v-icon>
                      </v-list-item-action>
                      <v-list-item-subtitle>Edit filter</v-list-item-subtitle>
                    </v-list-item>
                  </template>
                  <ts-filter-menu app :selected-chip="chip" @updateChip="updateChip($event, chip)"></ts-filter-menu>
                </v-menu>
                <v-list-item @click="copyFilterChip(chip)">
                  <v-list-item-action>
                    <v-icon>mdi-content-copy</v-icon>
                  </v-list-item-action>
                  <v-list-item-subtitle>Copy filter</v-list-item-subtitle>
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
          <v-btn v-if="index + 1 < timeFilterChips.length" icon small style="margin-top: 2px" class="mr-2">OR</v-btn>
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
              <v-btn small text rounded color="primary" v-bind="attrs" v-on="on">
                <v-icon left small> mdi-clock-plus-outline </v-icon>
                Add timefilter
              </v-btn>
            </template>

            <ts-filter-menu app @cancel="timeFilterMenu = false" @addChip="addChip"></ts-filter-menu>
          </v-menu>
        </span>
      </div>

      <!-- Term filters -->
      <div v-if="filterChips.length && isLucene" class="mt-1">
        <v-chip-group column>
          <span v-for="(chip, index) in filterChips" :key="index + chip.value">
            <v-tooltip top :disabled="chip.value.length < 33" open-delay="300">
              <template v-slot:activator="{ on: onTooltip, attrs }">
                <v-chip
                  outlined
                  close
                  close-icon="mdi-close"
                  @click:close="removeChip(chip)"
                  @click="copyFilterChip(chip)"
                  v-bind="attrs"
                  v-on="onTooltip"
                >
                  <v-icon v-if="chip.value === '__ts_star'" left small color="amber">mdi-star</v-icon>
                  <v-icon v-if="chip.value === '__ts_comment'" left small>mdi-comment-multiple-outline</v-icon>
                  <v-icon v-if="getQuickTag(chip.value)" left small :color="getQuickTag(chip.value).color">{{
                    getQuickTag(chip.value).label
                  }}</v-icon>
                  <span v-if="chip.operator === 'must_not'" class="filter-chip-truncate">
                    <span style="color: red">NOT </span>
                    {{ (chip.field ? `${chip.field} : ${chip.value}` : chip.value) | formatLabelText }}
                  </span>
                  <span v-else class="filter-chip-truncate">
                    {{ (chip.field ? `${chip.field} : ${chip.value}` : chip.value) | formatLabelText }}
                  </span>
                </v-chip>
              </template>
              <span>{{ chip.value }}</span>
            </v-tooltip>
            <v-btn v-if="index + 1 < timeFilterChips.length" icon small style="margin-top: 2px" class="mr-2">AND</v-btn>
          </span>
        </v-chip-group>
      </div>
    </v-card>

    <!-- Eventlist -->
    <v-card flat class="mt-5 mx-3" color="transparent">
      <ts-event-list
        v-if="queryLanguage === 'lucene'"
        :query-request="activeQueryRequest"
        :search-mode="searchMode"
        @countPerIndex="updateCountPerIndex($event)"
        @countPerTimeline="updateCountPerTimeline($event)"
      ></ts-event-list>

      <!-- Owns its own fetch and result state, the same way ts-event-list does
           for Lucene searches. -->
      <ts-direct-query-panel
        v-else
        :query-request="activeDirectQueryRequest"
        :language="queryLanguage"
        :cancel-token="directQueryCancelToken"
        :explain-request="activeDirectQueryExplainRequest"
        @loading="directQueryLoading = $event"
      ></ts-direct-query-panel>
    </v-card>
  </v-container>
</template>

<script>
import ApiClient from '../utils/RestApiClient.js'
import EventBus from '../event-bus.js'

import { dragscroll } from 'vue-dragscroll'

import TsSearchHistoryTree from '../components/Explore/SearchHistoryTree.vue'
import TsSearchHistoryButtons from '../components/Explore/SearchHistoryButtons.vue'
import TsSearchDropdown from '../components/Explore/SearchDropdown.vue'
import TsTimelinePicker from '../components/Explore/TimelinePicker.vue'
import TsFilterMenu from '../components/Explore/FilterMenu.vue'
import TsUploadTimelineFormButton from '../components/UploadFormButton.vue'
import TsAddManualEvent from '../components/Explore/AddManualEvent.vue'
import TsEventList from '../components/Explore/EventList.vue'
import TsSearchHelpCard from '../components/Explore/SearchHelpCard.vue'
import TsDirectQueryPanel from '../components/Explore/DirectQueryPanel.vue'
import TsDirectQueryEditor from '../components/Explore/DirectQueryEditor.vue'
import TsSearchModeToggle from '../components/Explore/SearchModeToggle.vue'

const defaultQueryFilter = () => {
  return {
    from: 0,
    terminate_after: 40,
    size: 40,
    indices: '_all',
    order: 'asc',
    chips: [],
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
    TsTimelinePicker,
    TsFilterMenu,
    TsUploadTimelineFormButton,
    TsAddManualEvent,
    TsEventList,
    TsSearchHelpCard,
    TsDirectQueryPanel,
    TsDirectQueryEditor,
    TsSearchModeToggle,
  },
  props: ['sketchId'],
  data() {
    return {
      countPerIndex: {},
      countPerTimeline: {},
      currentItemsPerPage: 40,
      timeFilterMenu: false,
      selectedFields: [{ field: 'message', type: 'text' }],
      showRightSidePanel: false,
      addManualEvent: false,
      datetimeManualEvent: '',
      params: {},
      contextEvent: false,
      originalContext: false,
      showSearchDropdown: false,
      activeQueryRequest: {},
      currentQueryString: '',
      currentQueryFilter: defaultQueryFilter(),
      selectedLabels: [],
      showSearchHistory: false,
      showSearchHelp: false,
      zoomLevel: 0.7,
      zoomOrigin: {
        x: 0,
        y: 0,
      },
      // TODO: Refactor this into a configurable option
      quickTags: [
        { tag: 'bad', color: 'red', textColor: 'white', label: 'mdi-alert-circle-outline' },
        { tag: 'suspicious', color: 'orange', textColor: 'white', label: 'mdi-help-circle-outline' },
        { tag: 'good', color: 'green', textColor: 'white', label: 'mdi-check-circle-outline' },
      ],
      showTimelines: true,
      queryLanguage: 'lucene',
      activeDirectQueryRequest: {},
      // Mirrored up from the panel so the editor can offer Run or Cancel.
      directQueryLoading: false,
      // Incremented to ask the panel to abort the request in flight.
      directQueryCancelToken: 0,
      // ISO strings from the editor's datetime-local fields, or empty for an
      // open end. Applied by the backend as a bound on the event timestamp.
      directQueryTimeRange: { start: '', end: '' },
      activeDirectQueryExplainRequest: {},
      localSearchMode: null,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    enabledTimelines() {
      return this.$store.state.enabledTimelines
    },
    meta() {
      return this.$store.state.meta
    },
    directQueryEnabled() {
      // PPL and SQL are served by the OpenSearch SQL plugin rather than the
      // search API, so the backend reports whether this cluster can run them
      // at all. Absent metadata means the sketch has not loaded yet, which is
      // treated as unavailable so the languages do not flicker into the menu.
      return !!(this.meta && this.meta.supports_direct_query)
    },
    // Gates the Lucene-only chrome. A direct query is sent as a query string
    // plus the enabled timeline ids and nothing else, so filter chips, the
    // timefilter menu and the saved-search dropdown have no effect on it and
    // would otherwise imply a narrowing that never reaches OpenSearch.
    isLucene() {
      return this.queryLanguage === 'lucene'
    },
    // Unified selector value backing the merged search-mode/query-language
    // toggle. PPL/SQL map to queryLanguage; query_string/wildcard map to the
    // Lucene searchMode (queryLanguage forced back to 'lucene').
    selectedSearchType: {
      get() {
        if (this.queryLanguage === 'ppl' || this.queryLanguage === 'sql') {
          return this.queryLanguage
        }
        return this.searchMode
      },
      set(value) {
        if (value === 'ppl' || value === 'sql') {
          this.queryLanguage = value
        } else {
          if (this.queryLanguage !== 'lucene') {
            this.queryLanguage = 'lucene'
          }
          this.searchMode = value
        }
      }
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
    activeContext() {
      return this.$store.state.activeContext
    },
    activeTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.active_timelines]
      return timelines.sort(function (a, b) {
        return a.name.localeCompare(b.name)
      })
    },
    userSettings() {
      return this.$store.state.settings
    },
    systemSettings() {
      return this.$store.state.systemSettings
    },
    searchMode: {
      get() {
        if (this.localSearchMode !== null) {
          return this.localSearchMode
        }
        if (this.meta && this.meta.supports_wildcard) {
          if (this.userSettings && this.userSettings.defaultSearchMethod) {
            return this.userSettings.defaultSearchMethod
          }
          if (this.systemSettings && this.systemSettings.OPENSEARCH_WILDCARD_DEFAULT) {
            return 'wildcard'
          }
        }
        return 'query_string'
      },
      set(value) {
        this.localSearchMode = value
        if (this.currentQueryString) {
          this.search()
        }
      }
    },
  },
  watch: {
    enabledTimelines: function () {
      this.updateEnabledTimelines(this.enabledTimelines)
    },
    queryLanguage: function () {
      // The panel clears its own results; drop the stale request so switching
      // languages doesn't re-run the previous one.
      this.activeDirectQueryRequest = {}
    },
    directQueryEnabled: function (enabled) {
      // The sketch metadata arrives after this view mounts, and a cluster can
      // lose the plugin between two loads. Either way a language the cluster
      // cannot serve must not stay selected.
      if (!enabled && !this.isLucene) {
        this.queryLanguage = 'lucene'
      }
    },
  },
  methods: {
    getQuickTag(tag) {
      return this.quickTags.find((el) => el.tag === tag)
    },
    updateCountPerIndex: function (count) {
      this.countPerIndex = count
    },
    updateCountPerTimeline: function (count) {
      this.countPerTimeline = count
    },
    directQueryRequest: function () {
      return {
        queryString: this.currentQueryString,
        timelineIds: this.enabledTimelines,
        startTime: this.directQueryTimeRange.start,
        endTime: this.directQueryTimeRange.end,
      }
    },
    carryOverDirectQueryTimeRange: function () {
      const start = this.directQueryTimeRange.start
      const end = this.directQueryTimeRange.end
      // A datetime_range chip needs both ends. Filling an open end with the
      // other bound would collapse the range to an instant, and inventing one
      // would filter on something the analyst never asked for, so a half-open
      // range is left behind instead.
      if (!start || !end) return
      // The editor's fields are UTC wall-clock without a zone; the chip is read
      // elsewhere as a full ISO instant.
      const value = new Date(start + 'Z').toISOString() + ',' + new Date(end + 'Z').toISOString()
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = []
      }
      const exists = this.currentQueryFilter.chips.find(
        (chip) => chip.type === 'datetime_range' && chip.value === value
      )
      if (exists) return
      this.currentQueryFilter.chips.push({
        field: '',
        type: 'datetime_range',
        value,
        operator: 'must',
        active: true,
      })
    },
    cancelDirectQuery: function () {
      this.directQueryCancelToken += 1
    },
    explainDirectQuery: function () {
      // A fresh object each time so re-explaining an unchanged query still
      // triggers the panel's watcher.
      this.activeDirectQueryExplainRequest = this.directQueryRequest()
    },
    toggleSearchHistory: function () {
      this.showSearchHistory = !this.showSearchHistory
      if (this.showSearchHistory) {
        this.triggerScrollTo()
      }
    },
    setQueryAndFilter: async function (searchEvent) {
      if (this.$route.name !== 'Explore') {
        this.$router.push({ name: 'Explore', params: { sketchId: this.sketch.id } })
      }
      // A chip raised while a PPL or SQL result is on screen is a pivot from an
      // aggregate row into the evidence behind it. The event list is Lucene
      // only, and the pipeline sitting in the search box is not a Lucene query,
      // so both the language and the query string are handed over before the
      // chip is applied.
      const pivotedFromDirectQuery = !this.isLucene
      if (pivotedFromDirectQuery) {
        this.queryLanguage = 'lucene'
        this.currentQueryString = ''
      }
      if (searchEvent.queryString) {
        this.currentQueryString = searchEvent.queryString
      }

      if (!this.currentQueryString && searchEvent.chip) {
        this.currentQueryString = '*'
      }

      // Preserve user defined filter instead of resetting, if it exist.
      if (!searchEvent.queryFilter) {
        searchEvent.queryFilter = this.currentQueryFilter
      }
      this.currentQueryFilter = searchEvent.queryFilter

      // Add any chips from the search event and make sure they are not in the
      // current filter already. E.g. don't add a star filter twice.
      if (searchEvent.chip) {
        // Matching on the value alone drops a second chip that carries the same
        // value on a different field, which a pivot hits whenever an identifier
        // reaches the results under more than one column name.
        const chipExist = this.currentQueryFilter.chips.find(
          (chip) =>
            chip.value === searchEvent.chip.value &&
            chip.field === searchEvent.chip.field &&
            chip.operator === searchEvent.chip.operator
        )
        if (!chipExist) {
          this.currentQueryFilter.chips.push(searchEvent.chip)
        }
      }

      // The bound the analyst set on the direct query is not part of the chip,
      // so without this the pivot would widen the investigation back out to the
      // whole timeline.
      if (pivotedFromDirectQuery) {
        this.carryOverDirectQueryTimeRange()
      }

      // Preserve user defined item count instead of resetting.
      this.currentQueryFilter.size = this.currentItemsPerPage
      this.currentQueryFilter.terminate_after = this.currentItemsPerPage

      // Run the search
      if (searchEvent.doSearch) {
        if (searchEvent.incognito) {
          this.search(true, true)
        } else {
          this.search()
        }
      } else {
        // Refocus the search input so the user can continue typing
        await this.$nextTick()
        if (this.$refs.searchInput) {
          this.$refs.searchInput.focus()
        }
      }
    },

    search: function (resetPagination = true, incognito = false, parent = false) {
      this.showSearchDropdown = false

      // PPL/SQL results are tabular rather than an event list, so the request
      // is handed to the direct query panel instead of ts-event-list.
      if (this.queryLanguage !== 'lucene') {
        this.activeDirectQueryRequest = this.directQueryRequest()
        return
      }

      let queryRequest = {}
      queryRequest.queryString = this.currentQueryString
      this.currentQueryFilter.use_wildcard_fields = (this.searchMode === 'wildcard')

      queryRequest.queryFilter = this.currentQueryFilter
      queryRequest.resetPagination = resetPagination
      queryRequest.incognito = incognito
      queryRequest.parent = parent
      this.activeQueryRequest = queryRequest
    },
    searchView: function (viewId) {
      this.showSearchDropdown = false

      if (this.$route.name !== 'Explore') {
        this.$router.push({ name: 'Explore', params: { sketchId: this.sketch.id } })
      }

      if (viewId !== parseInt(viewId, 10) && typeof viewId !== 'string') {
        viewId = viewId.id
      }

      ApiClient.getView(this.sketchId, viewId)
        .then((response) => {
          let view = response.data.objects[0]
          this.currentQueryString = view.query_string
          this.currentQueryFilter = JSON.parse(view.query_filter)
          if (this.currentQueryFilter && this.currentQueryFilter.use_wildcard_fields) {
            this.localSearchMode = 'wildcard'
          } else {
            this.localSearchMode = 'query_string'
          }
          if (!this.currentQueryFilter.fields || !this.currentQueryFilter.fields.length) {
            this.currentQueryFilter.fields = [{ field: 'message', type: 'text' }]
          }
          this.selectedFields = this.currentQueryFilter.fields
          let chips = this.currentQueryFilter.chips
          if (chips) {
            for (let i = 0; i < chips.length; i++) {
              if (chips[i].type === 'label') {
                this.selectedLabels.push(chips[i].value)
              }
            }
          }
          this.contextEvent = false
          this.search()
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
    updateEnabledTimelines: function (timelineIds) {
      this.currentQueryFilter.indices = timelineIds
      this.search()
    },
    toggleChip: function (chip) {
      // Treat undefined as active to support old chip formats.
      if (chip.active === undefined) {
        chip.active = true
      }
      chip.active = !chip.active
      this.search()
    },
    copyFilterChip(chip) {
      let textToCopy = ''
      // Different handling based on chip type
      if (chip.type.startsWith('datetime')) {
        // For datetime chips, just copy the value
        textToCopy = chip.value
      } else {
        // For other chips, copy both field and value
        textToCopy =
          chip.operator === 'must_not'
            ? `NOT ${chip.field ? `${chip.field}:` : ''}"${chip.value}"`
            : `${chip.field ? `${chip.field}:` : ''}"${chip.value}"`
      }
      // Copy to clipboard
      navigator.clipboard
        .writeText(textToCopy)
        .then(() => {
          this.infoSnackBar('Copied to clipboard!')
        })
        .catch((e) => {
          this.errorSnackBar('Failed to copy to clipboard.')
          console.error(e)
        })
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
    jumpInHistory: function (node) {
      this.currentQueryString = node.query_string
      this.currentQueryFilter = JSON.parse(node.query_filter)
      if (this.currentQueryFilter && this.currentQueryFilter.use_wildcard_fields) {
        this.localSearchMode = 'wildcard'
      } else {
        this.localSearchMode = 'query_string'
      }
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
      this.search(true, true, node.id)
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
    enableAllTimelines() {
      this.$store.dispatch(
        'updateEnabledTimelines',
        this.activeTimelines.map((tl) => tl.id)
      )
    },
    disableAllTimelines() {
      this.$store.dispatch('updateEnabledTimelines', [])
    },
  },
  mounted() {
    // The Lucene input is not rendered in PPL/SQL mode. The language always
    // starts as Lucene so it is there on first mount, but the ref is
    // conditional, and setQueryAndFilter() guards it the same way.
    if (this.$refs.searchInput) {
      this.$refs.searchInput.focus()
    }
    EventBus.$on('setQueryAndFilter', this.setQueryAndFilter)
    EventBus.$on('setActiveView', this.searchView)
  },
  beforeDestroy() {
    EventBus.$off('setQueryAndFilter')
    EventBus.$off('setActiveView')
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

.filter-chip-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}

.expanded .timeline-header {
  .v-icon.open-indicator {
    display: inline;
  }
  .v-icon.closed-indicator {
    display: none;
  }
}
.timeline-header {
  display: flex;
  align-items: center;

  .v-icon.open-indicator {
    display: none;
  }
}
</style>
