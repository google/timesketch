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
  <table class="table is-fullwidth">
    <thead>
      <th width="220"></th>
      <th width="1"></th>
      <th v-for="(field, index) in selectedFields" :key="index">{{ field.field }}</th>
      <th width="150">Timeline name</th>
    </thead>
    <ts-sketch-explore-event-list-row
      v-for="(event, index) in eventList.objects"
      :key="index"
      :event="event"
      :prevEvent="eventList.objects[index - 1]"
      :selected-fields="selectedFields"
      :display-options="displayOptions"
      :display-controls="false">
    </ts-sketch-explore-event-list-row>
  </table>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsSketchExploreEventListRow from './EventListRow'

export default {
  components: {
    TsSketchExploreEventListRow
  },
  props: ['view', 'queryDsl', 'queryFilter'],
  data () {
    return {
      eventList: [],
      selectedFields: [],
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
    }
  },
  methods: {
    search: function (queryDsl, queryFilter={}) {
      if (!Object.keys(queryFilter).length) {
        queryFilter = {}
        this.selectedFields = [{field: 'message', type: 'text'}]
      }

      let formData = {
        'dsl': queryDsl,
        'filter': queryFilter
      }

      ApiClient.search(this.sketch.id, formData).then((response) => {
        this.eventList = response.data
      }).catch((e) => {})
    },
    searchView: function (viewId) {
      ApiClient.getView(this.sketch.id, viewId).then((response) => {
        let view = response.data.objects[0]
        let queryDsl = view.query_string
        let queryFilter = JSON.parse(view.query_filter)
        if (!queryFilter.fields || !queryFilter.fields.length) {
          queryFilter.fields = [{field: 'message', type: 'text'}]
        }
        this.selectedFields = queryFilter.fields
        this.search(queryDsl, queryFilter)
      }).catch((e) => {})
    }
  },
  created: function () {
    if (this.view) {
      this.searchView(this.view.id)
    }
    if (this.queryDsl) {
      this.search(this.queryDsl)
    }
  },
  watch: {
    queryDsl: function (queryDsl) {
      this.search(queryDsl)
    }
  }
}
</script>
