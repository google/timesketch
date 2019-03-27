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
  <form v-on:submit.prevent="search">
    <input v-model="currentQueryString" class="ts-search-input" type="text" placeholder="Search" autofocus>
  </form>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

export default {
  name: 'ts-sketch-explore-search',
  props: ['sketchId'],
  data () {
    return {
      params: {}
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
      ApiClient.getView(this.sketchId, viewId).then((response) => {
        let view = response.data.objects[0]
        this.currentQueryString = view.query_string
        this.currentQueryFilter = JSON.parse(view.query_filter)
        this.search()
      }).catch((e) => {})
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
