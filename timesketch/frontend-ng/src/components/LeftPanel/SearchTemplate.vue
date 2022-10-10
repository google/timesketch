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
    <v-row no-gutters class="pa-3" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
      <div @click="expanded = !expanded" style="cursor: pointer; font-size: 0.9em">
        <v-icon v-if="!expanded">mdi-chevron-right</v-icon>
        <v-icon v-else>mdi-chevron-down</v-icon>
        {{ searchtemplate.name }}
      </div>
      <v-spacer></v-spacer>
      <div><v-icon>mdi-dots-vertical</v-icon></div>
    </v-row>

    <v-expand-transition>
      <div v-show="expanded" class="pa-4 pt-0">
        <div style="font-size: 0.9em">
          <ul>
            <li>Description: {{ searchTemplateSpec.description }}</li>
            <li>Author: {{ searchTemplateSpec.author }}</li>
            <li>Date: {{ searchTemplateSpec.date }}</li>
            <li>References: {{ searchTemplateSpec.references }}</li>
          </ul>
        </div>

        <div v-if="parameters.length" class="pt-3">
          <div class="mb-3"><strong class="mb-3">Required input parameters</strong></div>
          <div class="mb-4" v-for="parameter in parameters" :key="parameter.name">
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

          <v-card-actions class="pl-0 mt-n3">
            <v-btn @click="parseQueryAndSearch()" small depressed color="primary" :disabled="!filledOut">
              Search
            </v-btn>
          </v-card-actions>
        </div>
        <div v-else class="mt-3">
          <v-btn @click="search(searchtemplate.query_string)" small depressed color="primary" :disabled="!filledOut"
            >Search</v-btn
          >
        </div>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
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
  created() {},
}
</script>

<style scoped lang="scss">
.hover:hover {
  background: red;
}
</style>
