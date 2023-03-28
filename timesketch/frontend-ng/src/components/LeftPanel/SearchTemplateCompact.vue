<!--
Copyright 2022 Google Inc. All rights reserved.

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
    <v-row no-gutters>
      <div
        style="width: 100%; border-radius: 4px; cursor: pointer"
        class="px-2 mb-n1"
        :class="[
          $vuetify.theme.dark ? 'dark-highlight' : 'light-highlight',
          $vuetify.theme.dark ? 'dark-hover-on-highlight' : 'light-hover-on-highlight',
        ]"
        @click="search(searchtemplate.query_string)"
      >
        <span style="font-size: 0.8em">{{ searchtemplate.name }}</span>
      </div>
    </v-row>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import EventBus from '../../main'

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
  props: ['searchtemplate'],
  data: function () {
    return {
      params: {},
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    parameters() {
      return JSON.parse(this.searchtemplate.template_json).parameters
    },
    filledOut() {
      return Object.keys(this.params).length === this.parameters.length
    },
    searchTemplateSpec() {
      return JSON.parse(this.searchtemplate.template_json)
    },
  },
  methods: {
    search(queryString) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = queryString
      eventData.queryFilter = defaultQueryFilter()
      EventBus.$emit('setQueryAndFilter', eventData)
    },
    parseQueryAndSearch() {
      let queryString
      ApiClient.parseSearchTemplate(this.searchtemplate.id, this.params)
        .then((response) => {
          queryString = response.data.objects[0].query_string
          this.search(queryString)
        })
        .catch((e) => {})
    },
  },
}
</script>

<style scoped lang="scss"></style>
