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
      <div class="container">
        <div class="card">
          <div class="card-content">

            <form v-on:submit.prevent="search">
              <input v-model="currentQueryString" class="ts-search-input" type="text" placeholder="Search" autofocus>
            </form>
            <br>

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

            <div class="field is-grouped">
              <p class="control">
                <ts-view-list-dropdown @setActiveView="searchView"></ts-view-list-dropdown>
              </p>
              <p class="control">
                <a class="button" v-on:click="showCreateViewModal = !showCreateViewModal">
                  <span class="icon is-small">
                    <i class="fas fa-save"></i>
                  </span>
                  <span>Save view</span>
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="card">
          <header class="card-header">
            <span class="card-header-title">
              <span class="icon is-small"><i class="fas fa-filter"></i></span>
              <span style="margin-left:10px;">Filters</span>
            </span>
          </header>
          <div class="card-content">
            <ts-explore-filter-time></ts-explore-filter-time>
            <br>
            <div style="margin-bottom: 8px;"><b>Timelines</b></div>
            <ts-explore-timeline-picker @doSearch="search" v-if="sketch.active_timelines"></ts-explore-timeline-picker>
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
import TsExploreTimelinePicker from './SketchExploreTimelinePicker'
import TsExploreFilterTime from './SketchExploreFilterTime'

export default {
  name: 'ts-sketch-explore-search',
  components: {
    TsViewListDropdown,
    TsCreateViewForm,
    TsExploreTimelinePicker,
    TsExploreFilterTime
  },
  props: ['sketchId'],
  data () {
    return {
      params: {},
      showCreateViewModal: false
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
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
      this.searchInProgress = true
      let formData = {
        'query': this.currentQueryString,
        'filter': this.currentQueryFilter
      }
      ApiClient.search(this.sketchId, formData).then((response) => {
        this.$store.commit('updateEventList', response.data)
        this.searchInProgress = false
      }).catch((e) => {})
    },
    searchView: function (viewId) {
      if (viewId !== parseInt(viewId, 10)) {
        viewId = viewId.id
      }
      this.$router.push({ name: 'SketchExplore', query: { view: viewId } })
      ApiClient.getView(this.sketchId, viewId).then((response) => {
        let view = response.data.objects[0]
        this.currentQueryString = view.query_string
        this.currentQueryFilter = JSON.parse(view.query_filter)
        this.search()
      }).catch((e) => {})
    },
    toggleCreateViewModal: function () {
      this.showCreateViewModal = !this.showCreateViewModal
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
