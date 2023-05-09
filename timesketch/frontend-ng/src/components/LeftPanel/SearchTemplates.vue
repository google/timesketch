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
      :style="searchtemplates && searchtemplates.length ? 'cursor: pointer' : ''"
      class="pa-4"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> <v-icon left>mdi-text-box-search-outline</v-icon> Search Templates </span>
      <span class="float-right" style="margin-right: 10px">
        <small
          ><strong>{{ searchtemplates.length }}</strong></small
        >
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded && searchtemplates.length">
        <v-data-iterator :items="searchtemplates" :items-per-page.sync="itemsPerPage" :search="search">
          <template v-slot:header>
            <v-toolbar flat>
              <v-text-field
                v-model="search"
                clearable
                hide-details
                outlined
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
        this.searchtemplates = response.data.objects[0]
        if (typeof this.searchtemplates === 'undefined') {
          this.searchtemplates = []
        }
      })
      .catch((e) => {})
  },
}
</script>

<style scoped lang="scss">
.v-text-field ::v-deep input {
  font-size: 0.9em;
}

.v-text-field ::v-deep label {
  font-size: 0.9em;
}
</style>
