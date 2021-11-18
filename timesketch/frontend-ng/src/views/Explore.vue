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
  <v-row>
    <v-col cols="12">
      <v-card outlined class="pa-md-4">
        <v-text-field
          @keyup.enter="search"
          v-model="currentQueryString"
          v-on:click="showSearchDropdown = true"
          hide-details
          label="Search"
          placeholder="Search"
          rounded
          dense
          single-line
          append-icon="mdi-magnify"
          class="shrink mx-4"
        >
        </v-text-field>
      </v-card>
    </v-col>
    <v-col cols="12">
      <v-card outlined class="pa-md-4">
        <v-data-table
          v-model="selectedEvents"
          :headers="headers"
          :items="eventList.objects"
          :loading="eventList.objects.length < 1"
          item-key="_id"
          loading-text="Searching... Please wait"
          show-select
          show-expand
        >
          <template v-slot:top> {{ fromEvent }}-{{ toEvent }} of {{ totalHits }} events ({{ totalTime }}s) </template>

          <template v-slot:expanded-item="{ headers, item }">
            <td :colspan="headers.length">
              <v-row>
                <v-col cols="8">
                  <v-card outlined class="my-md-4">
                    <v-simple-table dense>
                      <template v-slot:default>
                        <thead>
                          <tr>
                            <th class="text-left">Attribute</th>
                            <th class="text-left">Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(value, key) in item._source" :key="key">
                            <td>{{ key }}</td>
                            <td>{{ value }}</td>
                          </tr>
                        </tbody>
                      </template>
                    </v-simple-table>
                  </v-card>
                </v-col>
                <v-col cols="4">
                  <v-sheet class="my-md-4"> Comments </v-sheet>
                </v-col>
              </v-row>
            </td>
          </template>

          <template v-slot:item.action="{ item }">
            <v-btn icon>
              <v-icon>mdi-star-outline</v-icon>
            </v-btn>
            <v-btn icon>
              <v-icon>mdi-tag-plus-outline</v-icon>
            </v-btn>
          </template>

          <template v-slot:item._source.datetime="{ item }">
            <v-menu offset-y :close-on-content-click="false">
              <template v-slot:activator="{ on, attrs }">
                <span v-bind:style="getTimelineColor(item)" v-bind="attrs" v-on="on" style="padding: 15px">{{
                  item._source.datetime
                }}</span>
              </template>
              <v-card class="mx-auto" max-width="344" outlined>
                <v-list-item three-line>
                  <v-list-item-content>
                    <div class="text-overline mb-4">OVERLINE</div>
                    <v-list-item-title class="text-h5 mb-1"> Headline 5 </v-list-item-title>
                    <v-list-item-subtitle>Greyhound divisely hello coldly fonwderfully</v-list-item-subtitle>
                  </v-list-item-content>

                  <v-list-item-avatar tile size="80" color="grey"></v-list-item-avatar>
                </v-list-item>

                <v-card-actions>
                  <v-btn outlined rounded text> Button </v-btn>
                </v-card-actions>
              </v-card>
            </v-menu>
          </template>

          <template v-slot:item._source.message="{ item }">
            <span class="ts-event-field-container">
              <span class="ts-event-field-ellipsis">
                {{ item._source.message }}
              </span>
            </span>
          </template>

          <template v-slot:item.timeline_name="{ item }">
            <v-chip>{{ getTimeline(item).name }}</v-chip>
          </template>
        </v-data-table>
      </v-card>
    </v-col>
  </v-row>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

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
  components: {},
  props: ['sketchId'],
  data() {
    return {
      headers: [
        { text: '', value: 'data-table-select' },

        {
          text: 'Datetime (UTC)',
          align: 'start',
          value: '_source.datetime',
          width: '255',
        },

        {
          text: '',
          value: 'action',
          align: 'start',
          width: '110',
        },

        {
          text: 'Message',
          align: 'start',
          value: '_source.message',
          width: '100%',
        },
        {
          text: 'Name',
          value: 'timeline_name',
          align: 'end',
        },
        { text: '', value: 'data-table-expand', align: 'end' },
      ],

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
      selectedEvents: [],
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
  },
  methods: {
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
    hideDropdown: function () {
      this.$refs['NewTimeFilter'].isActive = false
    },
    search: function (emitEvent = true, resetPagination = true, incognito = false, parent = false) {
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
        .then((response) => {
          this.eventList.objects = response.data.objects
          this.eventList.meta = response.data.meta
          this.searchInProgress = false

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
      this.$refs.searchInput.focus()
      if (searchEvent.doSearch) {
        this.search()
      }
    },
    exportSearchResult: function () {
      this.loadingOpen()
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
          this.loadingClose()
        })
    },
    searchView: function (viewId) {
      // Reset selected events.
      this.selectedEvents = {}

      this.showSearchDropdown = false
      this.showSaveSearchModal = false

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
    scrollToContextEvent: function () {
      this.$scrollTo('#' + this.contextEvent._id, 200, { offset: -300 })
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
    paginate: function (pageNum) {
      this.currentQueryFilter.from = pageNum * this.currentQueryFilter.size - this.currentQueryFilter.size
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
    updateSelectedEvents: function (event) {
      let key = event._index + ':' + event._id
      if (event.isSelected) {
        this.$set(this.selectedEvents, key, event)
      } else {
        this.$delete(this.selectedEvents, key)
      }
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
  },

  watch: {
    numEvents: function (newVal) {
      this.currentQueryFilter.size = newVal
      this.search(false, true, true)
    },
  },
  mounted() {
    this.$refs.searchInput.focus()
    this.showSearchDropdown = true
    EventBus.$on('eventSelected', (eventData) => {
      this.updateSelectedEvents(eventData)
    })
    EventBus.$on('clearSelectedEvents', () => {
      this.selectedEvents = {}
    })
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
</style>
