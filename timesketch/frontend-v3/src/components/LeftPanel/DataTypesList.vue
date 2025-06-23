<!--
Copyright 2025 Google Inc. All rights reserved.

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
    <v-data-iterator
      :items="dataTypes"
      v-model:items-per-page="itemsPerPage"
      :search="search"
      :hide-default-footer="dataTypes.length <= itemsPerPage"
    >
      <template v-slot:header v-if="dataTypes.length > itemsPerPage">
        <v-toolbar variant="flat">
          <v-text-field
            v-model="search"
            clearable
            hide-details
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-magnify"
            label="Search for a data type.."
          ></v-text-field>
        </v-toolbar>
      </template>

      <template v-slot:default="{ items }">
        <div
          v-for="item in items"
          :key="item.raw.data_type"
          @click="setQueryAndFilter(item.raw.data_type)"
          style="cursor: pointer; font-size: 0.9em"
        >
          <v-row no-gutters class="pa-2 pl-5" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
            <span
              >{{ item.raw.data_type }} (<small
                ><strong>{{ $filters.compactNumber(item.raw.count) }}</strong></small
              >)</span
            >
          </v-row>
        </div>
      </template>
    </v-data-iterator>
  </div>
</template>

<script>
import EventBus from '../../event-bus.js'
import { useAppStore } from '@/stores/app'

export default {
  name: 'DataTypesList',
  data: function () {
    return {
      appStore: useAppStore(),
      itemsPerPage: 10,
      search: '',
    }
  },
  computed: {
    dataTypes() {
      if (!this.appStore.dataTypes) return []
      // Sort the data types alphabetically
      return [...this.appStore.dataTypes].sort((a, b) => a.data_type.localeCompare(b.data_type))
    },
  },
  methods: {
    setQueryAndFilter(dataType) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = 'data_type:' + '"' + dataType + '"'
      EventBus.$emit('setQueryAndFilter', eventData)
      this.$emit('search-triggered')
    },
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
