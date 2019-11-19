<!--
Copyright 2019 Google Inc. All rights reserved.

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
    <section class="section">
        <div class="container is-fluid">
          <ts-navbar-secondary currentAppContext="sketch" currentPage="explore"></ts-navbar-secondary>
        </div>
    </section>

    <b-modal :active.sync="showCreateViewModal" :width="640" scroll="keep">
      <div class="card">
        <header class="card-header">
          <p class="card-header-title">Create new view</p>
        </header>
        <div class="card-content">
          <div class="content">
            <ts-create-view-form @toggleCreateViewModal="toggleCreateViewModal" :sketchId="sketchId" :currentQueryString="currentQueryString" :currentQueryFilter="currentQueryFilter"></ts-create-view-form>
          </div>
        </div>
      </div>
    </b-modal>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <header class="card-header" v-on:click="showSearch = !showSearch" style="cursor: pointer">
            <span class="card-header-title">
              <span class="icon is-small"><i class="fas fa-search"></i></span>
              <span style="margin-left:10px;">Search</span>
            </span>

            <a style="margin-top:10px;" class="button is-rounded is-small" v-on:click="showCreateViewModal = !showCreateViewModal">
              <span class="icon is-small">
                <i class="fas fa-save"></i>
              </span>
              <span>Save</span>
            </a>

            <span class="card-header-icon">
              <span class="icon">
                <i class="fas fa-angle-down" v-if="!showSearch" aria-hidden="true"></i>
                <i class="fas fa-angle-up" v-if="showSearch" aria-hidden="true"></i>
              </span>
            </span>

          </header>

          <div class="card-content" v-if="showSearch">

            <form v-on:submit.prevent="search" style="width:100%;">
              <input v-model="currentQueryString" class="ts-search-input" type="text" placeholder="Search" autofocus>
            </form>

            <div class="field is-grouped" style="margin-top:15px; margin-bottom: 25px;">

              <p class="control">
                <ts-view-list-dropdown @setActiveView="searchView" is-rounded="true"></ts-view-list-dropdown>
              </p>

              <p class="control">
                <b-dropdown trap-focus aria-role="menu">
                  <a class="button is-text" slot="trigger" role="button">
                    <span>+ Time range</span>
                  </a>
                  <b-dropdown-item custom :focusable="false" style="min-width: 500px; padding: 30px;">
                    <strong>Add time range</strong>
                    <br>
                    <br>
                    <ts-explore-filter-time @addChip="addChip($event)"></ts-explore-filter-time>
                  </b-dropdown-item>
                </b-dropdown>
              </p>

              <p class="control">
                <b-dropdown trap-focus aria-role="menu">
                  <a class="button is-text" slot="trigger" role="button">
                    <span>+ Filter</span>
                  </a>
                  <b-dropdown-item custom :focusable="false" style="min-width: 500px; padding: 30px;">
                    <strong>Add filter</strong>
                    <br>
                    <br>
                    <b-switch type="is-info" v-model="activeStarFilter" v-on:input="toggleLabelChip('__ts_star')">
                      <span style="margin-right:5px;" class="icon is-small"><i class="fas fa-star" style="color:#ffe300;-webkit-text-stroke-width: 1px;-webkit-text-stroke-color: silver;"></i></span>Show only starred events
                    </b-switch>
                  </b-dropdown-item>
                </b-dropdown>
              </p>

            </div>

            <div class="tags" style="margin-bottom: 5px;">
              <span v-for="(chip, index) in currentQueryFilter.chips" :key="index">
                <span v-if="chip.type === 'datetime_range'" class="tag is-light is-rounded" style="margin-right:7px;">
                  <span class="icon is-small" style="margin-right:7px;"><i class="fas fa-clock"></i></span> <span>{{ chip.value.split(',')[0] }}</span> <span v-if="chip.value.split(',')[0] !== chip.value.split(',')[1]">&rarr; {{ chip.value.split(',')[1] }}</span>
                  <button style="margin-left:7px" class="delete is-small" v-on:click="removeChip(index)"></button>
                </span>
              </span>
            </div>

            <div class="tags">
              <span v-for="(chip, index) in currentQueryFilter.chips" :key="index">
                <span v-if="chip.type !== 'datetime_range'" class="tag is-light is-rounded" style="margin-right:7px;">
                  <span v-if="chip.value === '__ts_star'" style="margin-right:7px;" class="icon is-small"><i class="fas fa-star" style="color:#ffe300;-webkit-text-stroke-width: 1px;-webkit-text-stroke-color: silver;"></i></span>
                  <span v-else-if="chip.type === 'label'" style="margin-right:7px;" class="icon is-small"><i class="fas fa-tag"></i></span>
                  <span style="margin-right:7px;">{{ chip | filterChip }}</span>
                  <button style="margin-left:7px" class="delete is-small" v-on:click="removeChip(index)"></button>
                </span>
              </span>
            </div>

            <ts-explore-timeline-picker v-if="sketch.active_timelines" @updateQueryFilter="updateQueryFilter($event)" :current-query-filter="currentQueryFilter"></ts-explore-timeline-picker>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <header class="card-header" v-on:click="showAggregations = !showAggregations" style="cursor: pointer">
            <span class="card-header-title">
              <span class="icon is-small"><i class="fas fa-chart-bar"></i></span>
              <span style="margin-left:10px;">Insights</span>
            </span>
            <span class="card-header-icon">
              <span class="icon">
                <i class="fas fa-angle-down" v-if="!showAggregations" aria-hidden="true"></i>
                <i class="fas fa-angle-up" v-if="showAggregations" aria-hidden="true"></i>
              </span>
            </span>
          </header>
          <div class="card-content" v-show="showAggregations">
            <ts-sketch-explore-aggregation></ts-sketch-explore-aggregation>
          </div>
        </div>
      </div>
    </section>

    <section class="section" id="context" v-show="contextEvent">
      <div class="container is-fluid">
        <b-message type="is-warning" aria-close-label="Close message">
          <strong>Context query</strong>
          <br><br>
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
                  <span v-if="toEvent && !searchInProgress">{{ fromEvent }}-{{ toEvent }} of {{ totalHits }} events ({{ totalTime }}s)</span>
                </div>
                <div class="level-item">
                  <span v-if="!toEvent && !searchInProgress">{{ totalHits }} events ({{ totalTime }}s)</span>
                </div>
                <div class="level-item" v-if="numSelectedEvents" style="margin-right:50px;">
                  <button class="button is-small is-outlined" style="border-radius: 4px;" v-on:click="toggleStar">
                    <span class="icon">
                      <i class="fas fa-star"></i>
                    </span>
                    <span>Toggle star ({{ numSelectedEvents }})</span>
                  </button>
                </div>
              </div>

              <!-- Right side -->
              <div class="level-right">

                <div class="level-item">
                  <div v-if="eventList.objects.length">
                    <b-pagination @change="paginate($event)"
                                  :total="totalHitsForPagination"
                                  :per-page="currentQueryFilter.size"
                                  :current.sync="currentPage"
                                  :simple=true
                                  size="is-small"
                                  icon-pack="fas"
                                  icon-prev="chevron-left"
                                  icon-next="chevron-right">
                    </b-pagination>
                  </div>
                </div>
                <div class="level-item">
                  <div v-if="eventList.objects.length" class="select is-small">
                    <select v-model="currentQueryFilter.size" @change="search">
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
                  <div v-if="eventList.objects.length" class="select is-small">
                    <select v-model="currentQueryFilter.order" @change="search">
                      <option v-bind:value="currentQueryFilter.order">{{ currentQueryFilter.order }}</option>
                      <option value="desc">desc</option>
                      <option value="asc">asc</option>
                    </select>
                  </div>
                </div>
                <div class="level-item">
                  <div v-if="eventList.objects.length">
                    <b-dropdown position="is-bottom-left" aria-role="menu" trap-focus :can-close="true">
                      <button class="button is-outlined is-small" style="border-radius: 4px;" slot="trigger">
                    <span class="icon is-small">
                      <i class="fas fa-table"></i>
                    </span>
                        <span>Fields ({{ selectedFields.length }})</span>
                      </button>
                      <b-dropdown-item aria-role="menu-item" :focusable="false" custom>
                        <div v-bind:class="{ tsdropdown: expandFieldDropdown }" style="width:300px;">
                          <multiselect style="display: block" v-if="meta.mappings" :options="meta.mappings" :value="selectedFieldsProxy" @open="expandFieldDropdown = true" @close="expandFieldDropdown = false" @input="updateSelectedFields" :multiple="true" :searchable="true" :close-on-select="false" label="field" track-by="field" placeholder="Add more fields ..."></multiselect>
                        </div>
                      </b-dropdown-item>
                      <b-dropdown-item aria-role="menu-item" :focusable="false" custom>
                    <span v-if="selectedFields.length">
                      <br>
                      <strong>Selected fields</strong>
                      <br><br>
                    </span>
                        <div class="tags">
                          <span v-for="(field, index) in selectedFields" :key="index">
                            <span class="tag is-light is-rounded" style="margin-right:7px;">
                              <span style="margin-right:7px;">{{ field.field }}</span>
                              <button style="margin-left:7px" class="delete is-small" v-on:click="removeField(index)"></button>
                            </span>
                          </span>
                        </div>

                        <hr>
                        <b-switch type="is-info" v-model="displayOptions.showTags">
                          <span>Show tags</span>
                        </b-switch>
                        <br>
                        <b-switch type="is-info" v-model="displayOptions.showEmojis">
                          <span>Show emojis</span>
                        </b-switch>

                      </b-dropdown-item>
                    </b-dropdown>
                  </div>
                </div>
              </div>
            </nav>

            <div v-if="searchInProgress"><span class="icon"><i class="fas fa-circle-notch fa-pulse"></i></span> Searching..</div>
            <div v-if="totalHits > 0" style="margin-top:20px;"></div>

            <ts-sketch-explore-event-list v-if="eventList.objects.length"
                                          :event-list="eventList.objects"
                                          :order="currentQueryFilter.order"
                                          :selected-fields="selectedFields"
                                          :display-options="displayOptions"
                                          @addChip="addChip($event)"
                                          @searchContext="searchContext($event)">
            </ts-sketch-explore-event-list>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsViewListDropdown from '../components/Sketch/ViewListDropdown'
import TsCreateViewForm from '../components/Sketch/CreateViewForm'
import TsSketchExploreEventList from '../components/Sketch/EventList'
import TsExploreTimelinePicker from '../components/Sketch/TimelinePicker'
import TsExploreFilterTime from '../components/Sketch/TimeFilter'
import TsExploreSessionChart from '../components/Sketch/SessionChart'
import TsSketchExploreAggregation from "../components/Sketch/Aggregation"
import EventBus from "../main"

export default {
  components: {
    TsSketchExploreAggregation,
    TsViewListDropdown,
    TsCreateViewForm,
    TsSketchExploreEventList,
    TsExploreTimelinePicker,
    TsExploreFilterTime,
    TsExploreSessionChart
  },
  props: ['sketchId'],
  data () {
    return {
      params: {},
      showCreateViewModal: false,
      showAggregations: false,
      showSearch: true,
      searchInProgress: false,
      activeStarFilter: false,
      currentPage: 1,
      contextEvent: false,
      originalContext: false,
      eventList: {
        meta: {},
        objects: []
      },
      currentQueryString: "",
      currentQueryFilter: {
        'from': 0,
        'time_start': null,
        'time_end': null,
        'terminate_after': 40,
        'size': 40,
        'indices': ['_all'],
        'order': 'asc',
        'chips': [],
        'fields': []
      },
      selectedFields: [{field: 'message', type: 'text'}],
      selectedFieldsProxy: [],
      expandFieldDropdown: false,
      selectedEvents: {},
      displayOptions: {
        showTags: true,
        showEmojis: true
      }
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    },
    totalHits () {
      return this.eventList.meta.es_total_count || 0
    },
    totalHitsForPagination () {
      let total = this.eventList.meta.es_total_count || 0
      // Elasticsearch only support pagination for the first 10k events.
      if (total > 9999) {
        total = 10000
      }
      return total
    },
    totalTime () {
      return this.eventList.meta.es_time / 1000 || 0
    },
    fromEvent () {
      return this.currentQueryFilter.from || 1
    },
    toEvent () {
      if (this.totalHits < this.currentQueryFilter.size) {
        return
      }
      return parseInt(this.currentQueryFilter.from) + parseInt(this.currentQueryFilter.size)
    },
    numSelectedEvents () {
      return Object.keys(this.selectedEvents).length
    }
  },
  methods: {
    search: function () {
      if (this.contextEvent) {
        // TODO: Make this selectable in the UI
        const contextTime = 300
        const numContextEvents = 500

        const dateTimeTemplate = 'YYYY-MM-DDTHH:mm:ss'
        let startDateTimeMoment = this.$moment.utc(this.contextEvent._source.datetime)
        let newStartDate = startDateTimeMoment.clone().subtract(contextTime, 's').format(dateTimeTemplate)
        let newEndDate = startDateTimeMoment.clone().add(contextTime, 's').format(dateTimeTemplate)
        let startChip = {
          'field': '',
          'value': newStartDate + ',' + startDateTimeMoment.format(dateTimeTemplate),
          'type': 'datetime_range',
          'operator': 'must'
        }
        let endChip = {
          'field': '',
          'value': startDateTimeMoment.format(dateTimeTemplate) + ',' + newEndDate,
          'type': 'datetime_range',
          'operator': 'must'
        }
        // TODO: Use chips instead
        this.currentQueryString = '* OR ' + '_id:' + this.contextEvent._id

        this.currentQueryFilter.chips = [startChip, endChip]
        this.currentQueryFilter.indices = [this.contextEvent._index]
        this.currentQueryFilter.size = numContextEvents

        // Scroll to the context box in the UI
        this.$scrollTo('#context', 200, {offset: -300})
      }

      // Reset selected events.
      this.selectedEvents = {}

      this.eventList = {
        meta: {},
        objects: []
      }

      let formData = {
        'query': this.currentQueryString,
        'filter': this.currentQueryFilter
      }

      ApiClient.search(this.sketch.id, formData).then((response) => {
        this.eventList.objects = response.data.objects
        this.eventList.meta = response.data.meta
      }).catch((e) => {})
    },
    searchView: function (viewId) {
      // Reset selected events.
      this.selectedEvents = {}

      if (viewId !== parseInt(viewId, 10) && typeof viewId !== 'string') {
        viewId = viewId.id
        this.$router.push({ name: 'SketchExplore', query: { view: viewId } })
      }
      ApiClient.getView(this.sketchId, viewId).then((response) => {
        let view = response.data.objects[0]
        this.currentQueryString = view.query_string
        this.currentQueryFilter = JSON.parse(view.query_filter)

        console.log(this.currentQueryFilter)

        if (!this.currentQueryFilter.fields.length) {
          this.currentQueryFilter.fields = [{field: 'message', type: 'text'}]
        }
        this.selectedFields = this.currentQueryFilter.fields
        if (this.currentQueryFilter.indices === '_all') {
          let allIndices = []
          this.sketch.active_timelines.forEach(function (timeline) {
            allIndices.push(timeline.searchindex.index_name)
          })
          this.currentQueryFilter.indices = allIndices
        }
        this.activeStarFilter = false
        let chips = this.currentQueryFilter.chips
        if (chips) {
          for (let i = 0; i < chips.length; i++) {
            if (chips[i].value === '__ts_star') {
              this.activeStarFilter = true
            }
          }
        }
        this.contextEvent = false
        this.search()
      }).catch((e) => {})
    },
    searchContext: function (event) {
      this.contextEvent = event
      if (!this.originalContext){
        let currentQueryStringCopy = JSON.parse(JSON.stringify(this.currentQueryString))
        let currentQueryFilterCopy = JSON.parse(JSON.stringify(this.currentQueryFilter))
        this.originalContext = {'queryString': currentQueryStringCopy, 'queryFilter': currentQueryFilterCopy}
      }
      this.search()
    },
    removeContext: function () {
      this.contextEvent = false
      this.currentQueryString = JSON.parse(JSON.stringify(this.originalContext.queryString))
      this.currentQueryFilter = JSON.parse(JSON.stringify(this.originalContext.queryFilter))
      this.search()
    },
    scrollToContextEvent: function () {
      this.$scrollTo('#' + this.contextEvent._id, 200, {offset: -300})
    },
    updateQueryFilter: function (filter) {
      this.currentQueryFilter = filter
      this.search()
    },
    toggleCreateViewModal: function () {
      this.showCreateViewModal = !this.showCreateViewModal
    },
    removeChip: function (chipIndex) {
      let chip = this.currentQueryFilter.chips[chipIndex]
      if (chip.value === '__ts_star') {
        this.activeStarFilter = false
      }
      this.currentQueryFilter.chips.splice(chipIndex, 1)
      this.search()
    },
    addChip: function (chip) {
      // Legacy views don't support chips so we need to add an array in order
      // to upgrade the view to the new filter system.
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = []
      }
      this.currentQueryFilter.chips.push(chip)
      this.showFilters = false
      this.search()
    },
    toggleLabelChip: function (labelName) {
      let chip = {
        'field': '',
        'value': labelName,
        'type': 'label',
        'operator': 'must'
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
    paginate: function (pageNum) {
      this.currentQueryFilter.from  = (pageNum * this.currentQueryFilter.size) - this.currentQueryFilter.size
      this.search()
    },
    updateSelectedFields: function (value) {
      // If we haven't fetched the field before, do an new search.
      value.forEach((field) => {
        if (!this.selectedFields.filter(e => e.field === field.field).length > 0) {
          this.search()
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
      ApiClient.saveEventAnnotation(this.sketch.id, 'label', '__ts_star', eventsToToggle).then((response) => {
      }).catch((e) => {})

      EventBus.$emit('toggleStar', this.selectedEvents)

    }
  },
  watch: {
    numEvents: function (newVal) {
      this.currentQueryFilter.size = newVal
      this.search()
    }
  },
  mounted () {
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
      indexName: this.$route.query.index,
      resultLimit: this.$route.query.limit,
      queryString: this.$route.query.q
    }

    if (this.params.viewId) {
      this.searchView(this.params.viewId)
    }

    if (this.params.queryString) {
      this.currentQueryString = this.params.queryString
      doSearch = true
    }

    if (this.params.indexName) {
      if (!this.params.queryString) {
        this.currentQueryString = '*'
      }
      this.currentQueryFilter.indices = [this.params.indexName]
      doSearch = true
    }

    if (doSearch) {
      this.search()
    }

  }
}
</script>

<style lang="scss">
  .ts-search-input {
    outline: none;
    border: none;
    font-size: 1.2em;
    border-radius: 5px;
    padding: 15px;
    background: #f9f9f9;
    width: 100%;
  }
  .dropdown-menu {
    box-shadow: 0 30px 30px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23);
  }

.multiselect,
.multiselect__input,
.multiselect__single {
  font-size: inherit;
}

.multiselect__option--highlight {
  background: #f5f5f5;
  color:#333;
}

.multiselect__option--highlight:after {
  background: #f5f5f5;
  color: #333;
}

.tsdropdown {
  min-height: 330px;
}

</style>
