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
    <div
      style="cursor: pointer"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
      class="pa-2"
    >
      <span>
        <v-icon v-if="!expanded">mdi-chevron-right</v-icon>
        <v-icon v-else>mdi-chevron-down</v-icon>
      </span>

      <span>Search Templates ({{ searchtemplates.length }})</span>
    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <v-divider></v-divider>
        <v-data-iterator :items="searchtemplates" :items-per-page.sync="itemsPerPage" :search="search">
          <template v-slot:header>
            <v-toolbar class="mb-1 mt-3" flat>
              <v-text-field
                v-model="search"
                clearable
                hide-details
                flat
                filled
                dense
                prepend-inner-icon="mdi-magnify"
                label="Search for a template.."
              ></v-text-field>
            </v-toolbar>
          </template>

          <template v-slot:default="props">
            <ts-search-template
              v-for="searchtemplate in props.items"
              :key="searchtemplate.id"
              :searchtemplate="searchtemplate"
            ></ts-search-template>
          </template>
        </v-data-iterator>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsSearchTemplate from './SearchTemplate.vue'

export default {
  props: [],
  components: {
    TsSearchTemplate,
  },
  data: function () {
    return {
      searchtemplates: [],
      expanded: false,
      itemsPerPage: 10,
      search: '',
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  created() {
    ApiClient.getSearchTemplates()
      .then((response) => {
        console.log('FOOBAR', response.data)
        this.searchtemplates = response.data.objects[0]
      })
      .catch((e) => {
        console.log('ERROR', e)
      })
  },
}
</script>
