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
    <div class="pa-4" flat :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
      <span style="cursor: pointer" @click="expanded = !expanded"
        ><v-icon left>mdi-database-outline</v-icon> Data Types ({{ dataTypes.length }})</span
      >
    </div>

    <v-expand-transition>
      <div v-show="expanded">
        <v-divider></v-divider>
        <v-row
          no-gutters
          v-for="dataType in dataTypes"
          :key="dataType.data_type"
          class="pa-3 pl-5"
          :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
        >
          <div @click="search(dataType.data_type)" style="cursor: pointer; font-size: 0.9em">
            <span>{{ dataType.data_type }} ({{ dataType.count | compactNumber }})</span>
          </div>
        </v-row>
      </div>
    </v-expand-transition>

    <v-divider></v-divider>
  </div>
</template>

<script>
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
  props: [],
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
