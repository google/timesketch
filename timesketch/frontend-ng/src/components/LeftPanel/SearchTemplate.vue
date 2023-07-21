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
    <v-row
      v-if="!parameters.length"
      @click="search(searchtemplate.query_string)"
      style="cursor: pointer; font-size: 0.9em"
      no-gutters
      class="pa-2 pl-5"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      {{ searchtemplate.name }}
    </v-row>

    <v-row
      v-else
      @click="expanded = !expanded"
      style="cursor: pointer; font-size: 0.9em"
      no-gutters
      class="pa-2 pl-5"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      {{ searchtemplate.name }}
    </v-row>

    <v-expand-transition>
      <div v-show="expanded" class="px-4">
        <div class="mt-2" v-for="parameter in parameters" :key="parameter.name">
          <v-text-field
            v-model="params[parameter.name]"
            :hint="parameter.description"
            :label="parameter.description"
            outlined
            dense
            hide-details
          >
          </v-text-field>
        </div>

        <v-card-actions class="pl-0">
          <v-btn @click="parseQueryAndSearch()" small depressed color="primary" :disabled="!filledOut"> Search </v-btn>
        </v-card-actions>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import EventBus from '../../main'

export default {
  props: ['searchtemplate'],
  data: function () {
    return {
      expanded: false,
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
