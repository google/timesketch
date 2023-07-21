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
      :style="dataTypes && dataTypes.length ? 'cursor: pointer' : ''"
      class="pa-4"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> <v-icon left>mdi-database-outline</v-icon> Data Types </span>
      <span class="float-right" style="margin-right: 10px">
        <small
          ><strong>{{ dataTypes.length }}</strong></small
        >
      </span>
    </div>

    <v-expand-transition>
      <div v-show="expanded && dataTypes.length">
        <v-data-iterator
          :items="dataTypes"
          :items-per-page.sync="itemsPerPage"
          :search="search"
          :hide-default-footer="dataTypes.length <= itemsPerPage"
        >
          <template v-slot:header v-if="dataTypes.length > itemsPerPage">
            <v-toolbar flat>
              <v-text-field
                v-model="search"
                clearable
                hide-details
                outlined
                dense
                prepend-inner-icon="mdi-magnify"
                label="Search for a data type.."
              ></v-text-field>
            </v-toolbar>
          </template>

          <template v-slot:default="props">
            <div
              v-for="dataType in props.items"
              :key="dataType.data_type"
              @click="setQueryAndFilter(dataType.data_type)"
              style="cursor: pointer; font-size: 0.9em"
            >
              <v-row no-gutters class="pa-2 pl-5" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
                <span
                  >{{ dataType.data_type }} (<small
                    ><strong>{{ dataType.count | compactNumber }}</strong></small
                  >)</span
                >
              </v-row>
            </div>
          </template>
        </v-data-iterator>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import EventBus from '../../main'

export default {
  props: [],
  data: function () {
    return {
      expanded: false,
      itemsPerPage: 10,
      search: '',
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    dataTypes() {
      return this.$store.state.dataTypes
    },
  },
  methods: {
    setQueryAndFilter(dataType) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = 'data_type:' + '"' + dataType + '"'
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
  created() {},
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
