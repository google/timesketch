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
    <ts-sketch-explore-event-list-item v-for="event in eventList.objects" :key="event._id" :event="event"></ts-sketch-explore-event-list-item>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsSketchExploreEventListItem from './SketchExploreEventListItem'

export default {
  name: 'ts-sketch-explore-view-event-list',
  components: {
    TsSketchExploreEventListItem
  },
  props: ['viewId'],
  data () {
    return {
      queryString: '',
      queryFilter: {},
      eventList: []
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    }
  },
  methods: {
    search: function () {
      let formData = {
        'query': this.queryString,
        'filter': this.queryFilter
      }
      ApiClient.search(this.sketch.id, formData).then((response) => {
        this.eventList = response.data
      }).catch((e) => {})
    },
    searchView: function (viewId) {
      ApiClient.getView(this.sketch.id, viewId).then((response) => {
        let view = response.data.objects[0]
        this.queryString = view.query_string
        this.queryFilter = JSON.parse(view.query_filter)
        this.search()
      }).catch((e) => {})
    }
  },
  created: function () {
    this.searchView(this.viewId)
  }
}
</script>

<style lang="scss"></style>
