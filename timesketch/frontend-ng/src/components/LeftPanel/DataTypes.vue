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
  <div v-if="dataTypes.length">
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

      <span style="font-size: 0.9em">Data Types ({{ dataTypes.length }})</span>
    </div>
    <div v-show="expanded">
      <v-divider></v-divider>
      <v-simple-table dense>
        <template v-slot:default>
          <tbody>
            <tr v-for="dataType in dataTypes" :key="dataType.data_type">
              <td @click="search(dataType.data_type)">
                <a>{{ dataType.data_type }}</a>
              </td>
              <td>{{ dataType.count | compactNumber }}</td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>
    </div>

    <v-divider></v-divider>
  </div>
</template>

<script>
import TsDataTypesTable from '../DataTypesTable.vue'

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
  props: ['facet'],
  components: { TsDataTypesTable },
  data: function () {
    return {
      expanded: false,
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
    search(dataType) {
      console.log('do a search from side panel')
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = 'data_type:' + '"' + dataType + '"'
      eventData.queryFilter = defaultQueryFilter()
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
  created() {},
}
</script>
