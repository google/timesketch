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
    <ts-navbar-main>
      <template v-slot:left>
        {{ sketch.name }}
      </template>
    </ts-navbar-main>

    <ts-navbar-secondary ref="navigation" currentAppContext="sketch" currentPage="explore"></ts-navbar-secondary>

    <b-modal :active.sync="showSaveSearchModal" :width="640" scroll="keep" style="z-index:999;">
      <div class="card">
        <header class="card-header">
          <p class="card-header-title">Save search</p>
        </header>
        <div class="card-content">
          <div class="content">
            <ts-create-view-form
              @setActiveView="searchView"
              :sketchId="sketchId"
              :currentQueryString="currentQueryString"
              :currentQueryFilter="currentQueryFilter"
            ></ts-create-view-form>
          </div>
        </div>
      </div>
    </b-modal>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content" v-if="showSearch">
            <div style="position:relative;">
              <div class="ts-search-box" style="z-index:998; position:absolute; width:100%;">
                <ts-search-history-buttons
                  style="position:absolute;top:7px;margin-left:10px;"
                ></ts-search-history-buttons>
                <input
                  @keyup.enter="search"
                  v-model="currentQueryString"
                  v-on:click="showSearchDropdown = true"
                  class="ts-search-input"
                  type="text"
                  ref="searchInput"
                  placeholder="Search"
                  style="padding-left:90px;"
                  autofocus
                  required
                />
                <div v-if="showSearchDropdown">
                  <ts-search-dropdown
                    :selected-labels="selectedLabels"
                    :query-string="currentQueryString"
                    @setActiveView="searchView"
                    @addChip="addChip"
                    @updateLabelChips="updateLabelChips()"
                    @close="closeSearchDropdown"
                    @close-on-click="showSearchDropdown = false"
                    @node-click="jumpInHistory"
                    @setQueryAndFilter="setQueryAndFilter"
                  >
                  </ts-search-dropdown>
                </div>
              </div>
            </div>

            <div class="field is-grouped" style="margin-top:60px;">
              <p class="control">
                <ts-dropdown width="500px">
                  <template v-slot:dropdown-trigger-element>
                    <a class="button is-text" style="text-decoration: none;" slot="trigger" role="button">
                      <span>+ Time filter</span>
                    </a>
                  </template>
                  <strong>Create time filter</strong>
                  <br />
                  <br />
                  <ts-explore-filter-time @addChip="addChip" @hideDropdown="hideDropdown"></ts-explore-filter-time>
                </ts-dropdown>
              </p>

              <p class="control">
                <ts-dropdown>
                  <template v-slot:dropdown-trigger-element>
                    <a class="button is-text" style="text-decoration: none;" role="button">
                      <span>+ Add label filter</span>
                    </a>
                  </template>

                  <div class="field">
                    <b-checkbox type="is-info" v-model="selectedLabels" native-value="__ts_star">
                      <span style="margin-right:5px;" class="icon is-small"
                        ><i
                          class="fas fa-star"
                          style="color:#ffe300;-webkit-text-stroke-width: 1px;-webkit-text-stroke-color: silver;"
                        ></i></span
                      >Show starred events
                    </b-checkbox>
                  </div>
                  <div class="field">
                    <b-checkbox type="is-info" v-model="selectedLabels" native-value="__ts_comment">
                      <span style="margin-right:5px;" class="icon is-small"><i class="fas fa-comment"></i></span>Show
                      events with comments
                    </b-checkbox>
                  </div>
                  <div class="level" style="margin-bottom: 5px;" v-for="label in filteredLabels" :key="label.label">
                    <div class="level-left">
                      <div class="field">
                        <b-checkbox type="is-info" v-model="selectedLabels" :native-value="label.label">
                          {{ label.label }}
                        </b-checkbox>
                      </div>
                    </div>
                  </div>
                  <br />
                  <button class="button is-info" v-on:click="updateLabelChips()">Add filter</button>
                </ts-dropdown>
              </p>
            </div>

            <p class="control" style="top:-40px;float:right;">
              <b-switch v-model="showHistogram" size="is-small" type="is-info" style="top:2px; margin-right:15px;"
                >Chart</b-switch
              >
              <b-switch
                v-model="showSearchHistory"
                v-on:input="triggerScrollTo"
                size="is-small"
                type="is-info"
                style="top:2px;"
                >Show history</b-switch
              >
            </p>

            <!-- Time filters -->
            <div class="tags" style="margin-bottom:-5px;">
              <span v-for="(chip, index) in timeFilterChips" :key="index + chip.value">
                <ts-dropdown width="500px" ref="TimeFilters">
                  <template v-slot:dropdown-trigger-element>
                    <span role="button" class="is-small is-outlined">
                      <div class="tags" style="margin-bottom: 5px; margin-right:7px;">
                        <span
                          class="tag is-medium"
                          style="cursor: pointer;"
                          v-bind:class="{ 'chip-disabled': chip.active === false }"
                        >
                          <span @click.stop="toggleChip(chip)">
                            <span v-if="index > 0" class="chip-operator-label">OR</span>
                            <span class="icon" style="margin-right:7px;"><i class="fas fa-clock"></i></span>
                            <span>{{ chip.value.split(',')[0] }}</span>
                            <span
                              v-if="
                                chip.type === 'datetime_range' && chip.value.split(',')[0] !== chip.value.split(',')[1]
                              "
                            >
                              &rarr; {{ chip.value.split(',')[1] }}</span
                            >
                          </span>
                          <span class="fa-stack fa-lg is-small" style="margin-left:5px; width:20px;">
                            <i class="fas fa-edit fa-stack-1x" style="transform:scale(0.7);color:#777;"></i>
                          </span>
                          <button
                            class="delete is-small"
                            style="margin-left:5px"
                            v-on:click="removeChip(chip)"
                          ></button>
                        </span>
                      </div>
                    </span>
                  </template>

                  <strong>Update time filter</strong>
                  <br />
                  <br />
                  <ts-explore-filter-time
                    :selectedChip="chip"
                    @updateChip="updateChip($event, chip)"
                    @hideDropdown="hideDropdown"
                  ></ts-explore-filter-time>
                </ts-dropdown>
              </span>
            </div>

            <!-- Label and term filter chips -->
            <div class="tags">
              <span v-for="(chip, index) in filterChips" :key="index + chip.value">
                <span
                  v-if="chip.type === 'label'"
                  class="tag is-medium"
                  style="margin-right:7px; cursor: pointer;"
                  v-bind:class="{ 'chip-disabled': chip.active === false }"
                  @click="toggleChip(chip, index)"
                >
                  <span v-if="index > 0 || timeFilterChips.length" class="chip-operator-label">AND</span>
                  <span v-if="chip.value === '__ts_star'" style="margin-right:7px;" class="icon is-small"
                    ><i
                      class="fas fa-star"
                      style="color:#ffe300;-webkit-text-stroke-width: 1px;-webkit-text-stroke-color: silver;"
                    ></i
                  ></span>
                  <span v-else-if="chip.value === '__ts_comment'" style="margin-right:7px;" class="icon is-small"
                    ><i class="fas fa-comment"></i
                  ></span>
                  <span v-else-if="chip.type === 'label'" style="margin-right:7px;" class="icon is-small"
                    ><i class="fas fa-tag"></i
                  ></span>
                  <span style="margin-right:7px;">{{ chip | filterChip }}</span>
                  <button style="margin-left:7px" class="delete is-small" v-on:click="removeChip(chip)"></button>
                </span>
                <span
                  v-if="chip.type === 'term'"
                  class="tag is-medium"
                  style="margin-right:7px; cursor: pointer;"
                  v-bind:class="{ 'chip-disabled': chip.active === false, 'is-danger': chip.operator === 'must_not' }"
                  @click="toggleChip(chip, index)"
                >
                  <span v-if="index > 0 || timeFilterChips.length" class="chip-operator-label">AND</span>
                  <span v-if="chip.operator === 'must_not'" class="chip-operator-label" style="font-weight:bold;"
                    >NOT</span
                  >
                  <span style="margin-right:7px;">{{ chip | filterChip }}</span>
                  <button style="margin-left:7px" class="delete is-small" v-on:click="removeChip(chip)"></button>
                </span>
              </span>
            </div>

            <ts-explore-timeline-picker
              v-if="sketch.active_timelines"
              @updateSelectedTimelines="updateSelectedTimelines($event)"
              :current-query-filter="currentQueryFilter"
              :count-per-index="eventList.meta.count_per_index"
              :count-per-timeline="eventList.meta.count_per_timeline"
            ></ts-explore-timeline-picker>
          </div>
        </div>
      </div>
    </section>

    <!-- Search history -->
    <section class="section" v-show="showSearchHistory">
      <div class="container is-fluid">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">
              My searches
            </p>
            <div class="card-header-icon" style="width:20%;">
              <span style="margin-right:10px;">Zoom</span>
              <b-slider
                style="margin-right:10px;"
                @dragend="triggerScrollTo"
                v-model="zoomLevel"
                format="percent"
                :min="0.1"
                :max="1"
                :step="0.01"
              ></b-slider>
            </div>
          </header>
          <div
            class="card-content no-scrollbars"
            v-dragscroll
            style="overflow: scroll; white-space: nowrap; max-height:700px;min-height:500px"
          >
            <ts-search-history-tree
              @node-click="jumpInHistory"
              :show-history="showSearchHistory"
              v-bind:style="{ transform: 'scale(' + zoomLevel + ')' }"
              style="transform-origin: top left;"
            ></ts-search-history-tree>
          </div>
        </div>
      </div>
    </section>

    <!-- Histogram -->
    <section class="section" v-if="showHistogram">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <ts-bar-chart
              :chart-data="eventList.meta.count_over_time"
              @addChip="addChipFromHistogram($event)"
            ></ts-bar-chart>
          </div>
        </div>
      </div>
    </section>

    <!-- Context search -->
    <section class="section" id="context" v-show="contextEvent">
      <div class="container is-fluid">
        <b-message type="is-warning" aria-close-label="Close message">
          <strong>Context query</strong>
          <br /><br />
          <div class="buttons">
            <button class="button" v-on:click="removeContext">&larr; Go back to original query</button>
            <button class="button" v-on:click="scrollToContextEvent">Help me find my event</button>
          </div>
        </b-message>
      </div>
    </section>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <nav class="level">
              <!-- Left side -->
              <div class="level-left">
                <div class="level-item">
                  <span v-if="toEvent && !searchInProgress"
                    >{{ fromEvent }}-{{ toEvent }} of {{ totalHits }} events ({{ totalTime }}s)</span
                  >
                </div>
                <div class="level-item">
                  <span v-if="!toEvent && !searchInProgress">{{ totalHits }} events ({{ totalTime }}s)</span>
                  <div v-if="searchInProgress">
                    <span class="icon"><i class="fas fa-circle-notch fa-pulse"></i></span> Searching..
                  </div>
                </div>
                <div class="level-item">
                  <button
                    class="button is-small is-outlined is-rounded"
                    v-if="totalHits > 0"
                    v-on:click="showSaveSearchModal = !showSavedSearchModal"
                  >
                    <span class="icon is-small"><i class="fas fa-save"></i></span>
                    <span>Save this search</span>
                  </button>
                </div>
                <div class="level-item" v-if="numSelectedEvents" style="margin-right:50px;">
                  <button class="button is-small is-outlined" style="border-radius: 4px;" v-on:click="toggleStar">
                    <span class="icon">
                      <i class="fas fa-star"></i>
                    </span>
                    <span>Star events ({{ numSelectedEvents }})</span>
                  </button>
                </div>
              </div>

              <!-- Right side -->
              <div class="level-right">
                <div class="level-item">
                  <b-pagination
                    @change="paginate($event)"
                    :total="totalHitsForPagination"
                    :per-page="currentQueryFilter.size"
                    :current.sync="currentPage"
                    :simple="true"
                    size="is-small"
                    icon-pack="fas"
                    icon-prev="chevron-left"
                    icon-next="chevron-right"
                  >
                  </b-pagination>
                </div>
                <div class="level-item">
                  <div class="select is-small">
                    <select
                      v-model="currentQueryFilter.size"
                      @change="search(true, true, true)"
                      style="border:1px solid var(--table-cell-border-color);"
                    >
                      <option v-bind:value="currentQueryFilter.size">{{ currentQueryFilter.size }}</option>
                      <option value="10">10</option>
                      <option value="20">20</option>
                      <option value="40">40</option>
                      <option value="80">80</option>
                      <option value="100">100</option>
                      <option value="200">200</option>
                      <option value="500">500</option>
                    </select>
                  </div>
                </div>
                <div class="level-item">
                  <button class="button is-small" style="border-radius: 4px;" v-on:click="changeSortOrder">
                    {{ currentQueryFilter.order }}
                  </button>
                </div>
                <div class="level-item">
                  <ts-dropdown position="is-bottom-left" width="300px">
                    <template v-slot:dropdown-trigger-element>
                      <button class="button is-small" style="border-radius: 4px;">
                        <span class="icon is-small">
                          <i class="fas fa-table"></i>
                        </span>
                        <span>Customize columns</span>
                      </button>
                    </template>

                    <multiselect
                      style="display: block;"
                      v-if="meta.mappings"
                      :options="meta.mappings"
                      :value="selectedFieldsProxy"
                      @open="expandFieldDropdown = true"
                      @close="expandFieldDropdown = false"
                      @input="updateSelectedFields"
                      :multiple="true"
                      :searchable="true"
                      :close-on-select="true"
                      label="field"
                      track-by="field"
                      placeholder="Add columns ..."
                    ></multiselect>

                    <span v-if="selectedFields.length">
                      <br />
                      <strong>Selected columns</strong>
                      <br /><br />
                    </span>
                    <div class="tags">
                      <span v-for="(field, index) in selectedFields" :key="index">
                        <span class="tag is-light is-rounded" style="margin-right:7px;">
                          <span style="margin-right:7px;">{{ field.field }}</span>
                          <button
                            style="margin-left:7px"
                            class="delete is-small"
                            v-on:click="removeField(index)"
                          ></button>
                        </span>
                      </span>
                    </div>

                    <br />
                    <b-switch type="is-info" v-model="displayOptions.showTags" style="margin-bottom:7px;">
                      <span>Show tags</span>
                    </b-switch>
                    <br />
                    <b-switch type="is-info" v-model="displayOptions.showEmojis" style="margin-bottom:7px;">
                      <span>Show emojis</span>
                    </b-switch>
                    <br />
                    <b-switch type="is-info" v-model="displayOptions.showMillis">
                      <span>Show microseconds</span>
                    </b-switch>
                  </ts-dropdown>
                </div>

                <div class="level-item">
                  <button
                    v-if="eventList.objects.length"
                    class="button is-small"
                    style="border-radius: 4px;"
                    v-on:click="exportSearchResult"
                  >
                    <span class="icon is-small" style="margin-right:5px;"><i class="fas fa-file-export"></i></span>
                    <span>Export to CSV</span>
                  </button>
                </div>
              </div>
            </nav>

            <div v-if="totalHits > 0" style="margin-top:20px;"></div>

            <ts-sketch-explore-event-list
              v-if="eventList.objects.length"
              :event-list="eventList.objects"
              :order="currentQueryFilter.order"
              :selected-fields="selectedFields"
              :display-options="displayOptions"
              @addChip="addChip($event)"
              @addLabel="updateLabelList($event)"
              @searchContext="searchContext($event)"
            >
            </ts-sketch-explore-event-list>

            <div v-if="eventList.objects.length" style="float:right;">
              <b-pagination
                @change="paginate($event)"
                :total="totalHitsForPagination"
                :per-page="currentQueryFilter.size"
                :current.sync="currentPage"
                :simple="true"
                size="is-small"
                icon-pack="fas"
                icon-prev="chevron-left"
                icon-next="chevron-right"
              >
              </b-pagination>
            </div>
            <br />
          </div>
        </div>
        <br />
      </div>
    </section>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsSketchExploreEventList from '../components/Explore/EventList'
import TsExploreTimelinePicker from '../components/Explore/TimelinePicker'
import TsExploreFilterTime from '../components/Explore/TimeFilter'
import TsSearchHistoryTree from '../components/Explore/SearchHistoryTree'
import TsSearchHistoryButtons from '../components/Explore/SearchHistoryButtons'
import TsBarChart from '../components/Aggregation/BarChart'
import TsSearchDropdown from '../components/Explore/SearchDropdown'
import TsCreateViewForm from '../components/Common/CreateViewForm'
import TsDropdown from '../components/Common/Dropdown'

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
    TsSketchExploreEventList,
    TsExploreTimelinePicker,
    TsExploreFilterTime,
    TsSearchHistoryTree,
    TsSearchHistoryButtons,
    TsBarChart,
    TsSearchDropdown,
    TsCreateViewForm,
    TsDropdown,
  },
  props: ['sketchId'],
  data() {
    return {
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
      showSearchDropdown: true,
      showSaveSearchModal: false,
      eventList: {
        meta: {},
        objects: [],
      },
      currentQueryString: '',
      currentQueryFilter: defaultQueryFilter(),
      selectedFields: [{ field: 'message', type: 'text' }],
      selectedFieldsProxy: [],
      expandFieldDropdown: false,
      selectedEvents: {},
      displayOptions: {
        showTags: true,
        showEmojis: true,
        showMillis: false,
      },
      selectedLabels: [],
      showSearchHistory: false,
      showHistogram: false,
      branchParent: None,
      zoomLevel: 1,
      zoomOrigin: {
        x: 0,
        y: 0,
      },
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    totalHits() {
      return this.eventList.meta.es_total_count_complete || 0
    },
    totalHitsForPagination() {
      let total = this.eventList.meta.es_total_count_complete || 0
      // Elasticsearch only support pagination for the first 10k events.
      if (total > 9999) {
        total = 10000
      }
      return total
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
      return Object.keys(this.selectedEvents).length
    },
    filterChips: function() {
      return this.currentQueryFilter.chips.filter(chip => chip.type === 'label' || chip.type === 'term')
    },
    timeFilterChips: function() {
      return this.currentQueryFilter.chips.filter(chip => chip.type.startsWith('datetime'))
    },
    filteredLabels() {
      return this.$store.state.meta.filter_labels.filter(label => !label.label.startsWith('__'))
    },
    currentSearchNode() {
      return this.$store.state.currentSearchNode
    },
  },
  methods: {
    hideDropdown: function() {
      this.$refs['NewTimeFilter'].isActive = false
    },
    search: function(emitEvent = true, resetPagination = true, incognito = false, parent = false) {
      this.searchInProgress = true
      if (!this.currentQueryString) {
        return
      }

      if (this.contextEvent) {
        // Scroll to the context box in the UI
        this.$scrollTo('#context', 200, { offset: -300 })
      }

      // Reset selected events.
      this.selectedEvents = {}

      this.eventList = emptyEventList()

      if (resetPagination) {
        // TODO: Can we keep position of the pagination when changing page size?
        // We need to calculate the new position in the page range and it is not
        // trivial with the current pagination UI component we use.
        this.currentQueryFilter.from = 0
        this.currentPage = 1
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
        .then(response => {
          this.eventList.objects = response.data.objects
          this.eventList.meta = response.data.meta
          this.searchInProgress = false

          if (!incognito) {
            EventBus.$emit('createBranch', this.eventList.meta.search_node)
            this.$store.dispatch('updateSearchHistory')
            this.branchParent = this.eventList.meta.search_node.id
          }
        })
        .catch(e => {})
    },
    setQueryAndFilter: function(searchEvent) {
      this.currentQueryString = searchEvent.queryString
      this.currentQueryFilter = searchEvent.queryFilter
      this.$refs.searchInput.focus()
      if (searchEvent.doSearch) {
        this.search()
      }
    },
    exportSearchResult: function() {
      this.loadingOpen()
      let formData = {
        query: this.currentQueryString,
        filter: this.currentQueryFilter,
        file_name: 'export.zip',
      }
      ApiClient.exportSearchResult(this.sketchId, formData)
        .then(response => {
          let fileURL = window.URL.createObjectURL(new Blob([response.data]))
          let fileLink = document.createElement('a')
          let fileName = 'export.zip'
          fileLink.href = fileURL
          fileLink.setAttribute('download', fileName)
          document.body.appendChild(fileLink)
          fileLink.click()
          this.loadingClose()
        })
        .catch(e => {
          console.error(e)
          this.loadingClose()
        })
    },
    searchView: function(viewId) {
      // Reset selected events.
      this.selectedEvents = {}

      this.showSearchDropdown = false
      this.showSaveSearchModal = false

      if (viewId !== parseInt(viewId, 10) && typeof viewId !== 'string') {
        viewId = viewId.id
        this.$router.push({ name: 'Explore', query: { view: viewId } })
      }
      ApiClient.getView(this.sketchId, viewId)
        .then(response => {
          let view = response.data.objects[0]
          this.currentQueryString = view.query_string
          this.currentQueryFilter = JSON.parse(view.query_filter)
          if (!this.currentQueryFilter.fields || !this.currentQueryFilter.fields.length) {
            this.currentQueryFilter.fields = [{ field: 'message', type: 'text' }]
          }
          this.selectedFields = this.currentQueryFilter.fields
          if (this.currentQueryFilter.indices[0] === '_all' || this.currentQueryFilter.indices === '_all') {
            let allIndices = []
            this.sketch.active_timelines.forEach(timeline => {
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
        .catch(e => {})
    },
    searchContext: function(event) {
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
      let newStartDate = startDateTimeMoment
        .clone()
        .subtract(contextTime, 's')
        .format(dateTimeTemplate)
      let newEndDate = startDateTimeMoment
        .clone()
        .add(contextTime, 's')
        .format(dateTimeTemplate)
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
    removeContext: function() {
      this.contextEvent = false
      this.currentQueryString = JSON.parse(JSON.stringify(this.originalContext.queryString))
      this.currentQueryFilter = JSON.parse(JSON.stringify(this.originalContext.queryFilter))
      this.search()
    },
    scrollToContextEvent: function() {
      this.$scrollTo('#' + this.contextEvent._id, 200, { offset: -300 })
    },
    updateSelectedTimelines: function(timelines) {
      let selected = []
      timelines.forEach(timeline => {
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
    clearSearch: function() {
      this.currentQueryString = ''
      this.currentQueryFilter = defaultQueryFilter()
      this.currentQueryFilter.indices = '_all'
      this.eventList = emptyEventList()
      this.$router.replace({ query: null })
    },
    toggleChip: function(chip) {
      // Treat undefined as active to support old chip formats.
      if (chip.active === undefined) {
        chip.active = true
      }
      chip.active = !chip.active
      this.search()
    },
    removeChip: function(chip, search = true) {
      let chipIndex = this.currentQueryFilter.chips.findIndex(c => c.value === chip.value)
      this.currentQueryFilter.chips.splice(chipIndex, 1)
      if (chip.type === 'label') {
        this.selectedLabels = this.selectedLabels.filter(label => label !== chip.value)
      }
      if (search) {
        this.search()
      }
    },
    updateChip: function(newChip, oldChip) {
      // Replace the chip at the given index
      let chipIndex = this.currentQueryFilter.chips.findIndex(c => c.value === oldChip.value && c.type === oldChip.type)
      this.currentQueryFilter.chips.splice(chipIndex, 1, newChip)
      this.search()
    },
    addChip: function(chip) {
      // Legacy views don't support chips so we need to add an array in order
      // to upgrade the view to the new filter system.
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = []
      }
      this.currentQueryFilter.chips.push(chip)
      this.search()
    },
    addChipFromHistogram: function(chip) {
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = []
      }
      this.currentQueryFilter.chips.forEach(chip => {
        if (chip.type === 'datetime_range') {
          this.removeChip(chip, false)
        }
      })
      this.addChip(chip)
    },
    toggleLabelChip: function(labelName) {
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
    updateLabelChips: function() {
      // Remove all current label chips
      this.currentQueryFilter.chips = this.currentQueryFilter.chips.filter(chip => chip.type !== 'label')
      this.selectedLabels.forEach(label => {
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
    updateLabelList: function(label) {
      if (this.meta.filter_labels.indexOf(label) === -1) {
        this.meta.filter_labels.push(label)
      }
    },
    paginate: function(pageNum) {
      this.currentQueryFilter.from = pageNum * this.currentQueryFilter.size - this.currentQueryFilter.size
      this.search(true, false, true)
    },
    updateSelectedFields: function(value) {
      // If we haven't fetched the field before, do an new search.
      value.forEach(field => {
        if (!this.selectedFields.filter(e => e.field === field.field).length > 0) {
          this.search(true, true, true)
        }
      })
      value.forEach(field => {
        this.selectedFields.push(field)
      })
      // Prevents tags from being displayed
      this.selectedFieldsProxy = []
    },
    removeField: function(index) {
      this.selectedFields.splice(index, 1)
    },
    updateSelectedEvents: function(event) {
      let key = event._index + ':' + event._id
      if (event.isSelected) {
        this.$set(this.selectedEvents, key, event)
      } else {
        this.$delete(this.selectedEvents, key)
      }
    },
    toggleStar: function() {
      // The function stars and unstars all selected events, instead of
      // toggling them. This helps when some of the selected events (but not
      // all) were already starred.
      let eventsStarred = []
      let eventsUnstarred = []
      let eventsToToggle = []
      Object.keys(this.selectedEvents).forEach((key, index) => {
        if (this.selectedEvents[key].isStarred) {
          eventsStarred.push(this.selectedEvents[key])
        }
        else {
          eventsUnstarred.push(this.selectedEvents[key])
        }
      })

      // Find out if there's a mix of starred and unstarred events
      if (eventsStarred.length && eventsUnstarred.length) {
        eventsToToggle = eventsUnstarred
      }
      else {
        eventsToToggle = (eventsUnstarred.length) ? eventsUnstarred : eventsStarred
      }

      // Updating has 3 independent parts:
      // 1) The backend via API
      ApiClient.saveEventAnnotation(this.sketch.id, 'label', '__ts_star', eventsToToggle, this.currentSearchNode)
        .then(response => {})
        .catch(e => {})
      // 2) The UI element representing each of the rows
      let idOfEventsToToggle = eventsToToggle.map(e => e._id)
      EventBus.$emit('toggleStar', idOfEventsToToggle)
      // 3) The local copy of events
      for (let event of eventsToToggle) {
        event.isStarred = !event.isStarred
      }
    },
    changeSortOrder: function() {
      if (this.currentQueryFilter.order === 'asc') {
        this.currentQueryFilter.order = 'desc'
      } else {
        this.currentQueryFilter.order = 'asc'
      }
      this.search(true, true, true)
    },
    loadingOpen: function() {
      this.loadingComponent = this.$buefy.loading.open({
        container: this.isFullPage ? null : this.$refs.element.$el,
      })
    },
    loadingClose: function() {
      this.loadingComponent.close()
    },
    jumpInHistory: function(node) {
      this.currentQueryString = node.query_string
      this.currentQueryFilter = JSON.parse(node.query_filter)
      if (!this.currentQueryFilter.fields || !this.currentQueryFilter.fields.length) {
        this.currentQueryFilter.fields = [{ field: 'message', type: 'text' }]
      }
      this.selectedFields = this.currentQueryFilter.fields
      if (this.currentQueryFilter.indices[0] === '_all' || this.currentQueryFilter.indices === '_all') {
        let allIndices = []
        this.sketch.active_timelines.forEach(timeline => {
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
    triggerScrollTo: function() {
      EventBus.$emit('triggerScrollTo')
    },
    zoomWithMouse: function(event) {
      // Add @wheel="zoomWithMouse" on element to activate.
      this.zoomOrigin.x = event.pageX
      this.zoomOrigin.y = event.pageY
      if (event.deltaY < 0) {
        this.zoomLevel += 0.07
      } else if (event.deltaY > 0) {
        this.zoomLevel -= 0.07
      }
    },
    closeSearchDropdown: function(targetElement) {
      // Prevent dropdown to close when the search input field is clicked.
      if (targetElement !== this.$refs.searchInput && targetElement.getAttribute('data-explore-element') === null) {
        this.showSearchDropdown = false
      }
    },
  },

  watch: {
    numEvents: function(newVal) {
      this.currentQueryFilter.size = newVal
      this.search(false, true, true)
    },
  },
  mounted() {
    this.$refs.searchInput.focus()
    this.showSearchDropdown = true
    EventBus.$on('eventSelected', eventData => {
      this.updateSelectedEvents(eventData)
    })
    EventBus.$on('clearSelectedEvents', () => {
      this.selectedEvents = {}
    })
  },
  created: function() {
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

      let timeline = this.sketch.active_timelines.find(timeline => {
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
.dropdown-menu {
  box-shadow: 0 30px 30px rgba(0, 0, 0, 0.19), 0 6px 6px rgba(0, 0, 0, 0.23);
}

.multiselect,
.multiselect__input,
.multiselect__single {
  font-size: inherit;
}

.multiselect__option--highlight {
  background: #f5f5f5;
  color: #333;
}

.multiselect__option--highlight:after {
  background: #f5f5f5;
  color: #333;
}

.tsdropdown {
  min-height: 330px;
}

.chip-disabled {
  text-decoration: line-through;
  opacity: 0.5;
}

.chip-operator-label {
  margin-right: 7px;
  font-size: 0.7em;
  cursor: default;
}

.can-change-background {
  color: rgba(10, 10, 10, 0.2);
}

.can-change-background:hover {
  color: rgba(10, 10, 10, 0.3);
}

.no-scrollbars::-webkit-scrollbar {
  display: none;
}

.no-scrollbars {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
