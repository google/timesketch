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

    <div class="modal" v-bind:class="{ 'is-active': showCreateViewModal }">>
      <div class="modal-background"></div>
      <div class="modal-content">
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
      </div>
      <button class="modal-close is-large" aria-label="close" v-on:click="showCreateViewModal = !showCreateViewModal"></button>
    </div>

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

              <div class="field is-grouped">
                <ts-view-list-dropdown @setActiveView="searchView"></ts-view-list-dropdown>
                <form v-on:submit.prevent="search" style="width:100%;">
                  <input v-model="currentQueryString" class="ts-search-input" type="text" placeholder="Search" autofocus>
                </form>
              </div>
              <br>

            <div class="tags">
              <span v-for="(chip, index) in currentQueryFilter.chips" :key="index" style="margin-right:7px;">
                <span v-if="chip.type === 'datetime_range'" class="tag is-light is-rounded is-medium">
                  <span class="icon is-small" style="margin-right:7px;"><i class="fas fa-clock"></i></span> <span>{{ chip.value.split(',')[0] }}</span> <span v-if="chip.value.split(',')[0] !== chip.value.split(',')[1]">&rarr; {{ chip.value.split(',')[1] }}</span>
                  <button style="margin-left:7px" class="delete is-small" v-on:click="removeChip(index)"></button>
                </span>
              </span>
              <span class="tag is-white is-rounded is-medium" style="cursor:pointer;" v-on:click="showFilters = !showFilters">+ Add time range</span>
            </div>

            <div v-show="showFilters">
              <ts-explore-filter-time @addChip="addChip($event)"></ts-explore-filter-time>
              <br>
            </div>

            <div class="tags">
              <span v-for="(chip, index) in currentQueryFilter.chips" :key="index">
                <span v-if="chip.type !== 'datetime_range'" class="tag is-light is-rounded is-small" style="margin-right:7px;">
                  <span v-if="chip.value === '__ts_star'" style="margin-right:7px;" class="icon is-small"><i class="fas fa-star" style="color:#ffe300;-webkit-text-stroke-width: 1px;-webkit-text-stroke-color: silver;"></i></span>
                  <span v-else-if="chip.type === 'label'" style="margin-right:7px;" class="icon is-small"><i class="fas fa-tag"></i></span>
                  <span style="margin-right:7px;">{{ chip | filterChip }}</span>
                  <button style="margin-left:7px" class="delete is-small" v-on:click="removeChip(index)"></button>
                </span>
              </span>

              <button class="tag is-small is-rounded" v-on:click="filterStarred"><span style="margin-right:5px;" class="icon is-small"><i class="fas fa-star" style="color:#ffe300;-webkit-text-stroke-width: 1px;-webkit-text-stroke-color: silver;"></i></span>Starred </button>

            </div>

            <ts-explore-timeline-picker @doSearch="search" v-if="sketch.active_timelines"></ts-explore-timeline-picker>

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

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <div v-if="!searchInProgress">{{ totalHits }} events ({{ totalTime }}s)</div>
            <div v-if="searchInProgress"><span class="icon"><i class="fas fa-circle-notch fa-pulse"></i></span> Searching..</div>
            <div v-if="totalHits > 0" style="margin-top:20px;"></div>
            <ts-sketch-explore-event-list></ts-sketch-explore-event-list>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsViewListDropdown from './SketchExploreViewListDropdown'
import TsCreateViewForm from './SketchCreateViewForm'
import TsSketchExploreEventList from './SketchExploreEventList'
import TsExploreTimelinePicker from './SketchExploreTimelinePicker'
import TsExploreFilterTime from './SketchExploreFilterTime'
import TsExploreSessionChart from './SketchExploreSessionChart'
import TsSketchExploreAggregation from "./SketchExploreAggregation"

export default {
  name: 'ts-sketch-explore-search',
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
      showFilters: false,
      showAggregations: false,
      showSearch: true
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    },
    eventList () {
      return this.$store.state.eventList
    },
    totalHits () {
      return this.eventList.meta.es_total_count || 0
    },
    totalTime () {
      return this.eventList.meta.es_time / 1000 || 0
    },
    searchInProgress: {
      get: function () {
        return this.$store.state.searchInProgress
      },
      set: function (isSearching) {
        this.$store.commit('updateSearchInProgress', isSearching)
      }
    },
    currentQueryString: {
      get: function () {
        return this.$store.state.currentQueryString
      },
      set: function (queryString) {
        if (queryString) {
          delete this.currentQueryFilter.star
        }
        this.$store.commit('updateCurrentQueryString', queryString)
      }
    },
    currentQueryFilter: {
      get: function () {
        return this.$store.state.currentQueryFilter
      },
      set: function (queryFilter) {
        this.$store.commit('updateCurrentQueryFilter', queryFilter)
      }
    }
  },
  methods: {
    search: function () {
      this.$store.commit('search', this.sketchId)
    },
    filterStarred: function () {
      let chip = {
          'field': '',
          'value': '__ts_star',
          'type': 'label',
          'operator': 'must'
        }
      this.addChip(chip)
    },
    searchView: function (viewId) {
      if (viewId !== parseInt(viewId, 10) && typeof viewId !== 'string') {
        viewId = viewId.id
        this.$router.push({ name: 'SketchExplore', query: { view: viewId } })
      }
      ApiClient.getView(this.sketchId, viewId).then((response) => {
        let view = response.data.objects[0]
        this.currentQueryString = view.query_string
        this.currentQueryFilter = JSON.parse(view.query_filter)
        if (this.currentQueryFilter.indices === '_all') {
          let allIndices = []
          this.sketch.active_timelines.forEach(function (timeline) {
            allIndices.push(timeline.searchindex.index_name)
          })
          this.currentQueryFilter.indices = allIndices
        }
        this.search()
      }).catch((e) => {})
    },
    toggleCreateViewModal: function () {
      this.showCreateViewModal = !this.showCreateViewModal
    },
    removeChip: function (chipIndex) {
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
    }
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
</style>
