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
    <div v-if="parameters.length" class="pa-2 pl-4" @click="expanded = !expanded" style="cursor: pointer">
      <v-menu open-on-hover offset-y :open-delay="1000" :close-on-content-click="false">
        <template v-slot:activator="{ on, attrs }">
          <a style="font-size: 0.9em" v-bind="attrs" v-on="on">{{ searchtemplate.name }}</a>
        </template>
        <v-card style="font-size: 0.9em" class="pa-3" width="400">
          {{ searchtemplate.description }}
        </v-card>
      </v-menu>
    </div>
    <div v-else @click="search(searchtemplate.query_string)" class="pa-2 pl-4" style="cursor: pointer">
      <a style="font-size: 0.9em" v-bind="attrs" v-on="on">{{ searchtemplate.name }}</a>
    </div>

    <v-expand-transition>
      <div v-show="expanded">
        <div style="font-size: 0.9em" class="pa-4 pt-3">
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
            <v-btn @click="parseQueryAndSearch()" small outlined color="primary" :disabled="!filledOut"> Search </v-btn>
          </v-card-actions>
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

<style scoped lang="scss"></style>
