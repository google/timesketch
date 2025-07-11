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
      v-model:page="page"
      :search="search"
    >
      <template v-slot:header>
        <div v-if="showSearch" class="pa-2">
          <v-text-field
            v-model="search"
            clearable
            hide-details
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-magnify"
            label="Search for a data type.."
          ></v-text-field>
        </div>
      </template>

      <template v-slot:default="{ items }">
        <div :style="containerStyles">
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
        </div>
      </template>

      <template v-slot:footer>
        <div v-if="!isScrollMode && numberOfPages > 1" class="d-flex justify-center pa-2">
          <v-pagination v-model="page" :length="numberOfPages" :total-visible="5" density="compact"></v-pagination>
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
  props: {
    mode: {
      type: String,
      default: 'paginate',
      validator: (val) => ['paginate', 'scroll'].includes(val),
    },
    searchThreshold: {
      type: Number,
      default: 10,
    },
    scrollHeight: {
      type: String,
      default: '500px',
    },
    pageSize: {
      type: Number,
      default: 10,
    },
  },
  data: function () {
    return {
      appStore: useAppStore(),
      itemsPerPage: this.pageSize,
      search: '',
      page: 1,
    }
  },
  computed: {
    dataTypes() {
      if (!this.appStore.dataTypes) return []
      return [...this.appStore.dataTypes].sort((a, b) => a.data_type.localeCompare(b.data_type))
    },
    isScrollMode() {
      return this.mode === 'scroll'
    },
    showSearch() {
      return this.dataTypes.length > this.searchThreshold
    },
    containerStyles() {
      if (this.isScrollMode) {
        return {
          maxHeight: this.scrollHeight,
          overflowY: 'auto',
        }
      }
      return {}
    },
    numberOfPages() {
      if (this.itemsPerPage <= 0) return 1
      return Math.ceil(this.dataTypes.length / this.itemsPerPage)
    },
  },
  watch: {
    mode: {
      immediate: true,
      handler(newVal) {
        if (newVal === 'scroll') {
          this.itemsPerPage = -1
        } else {
          this.itemsPerPage = this.pageSize
        }
      },
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

<style scoped lang="scss"></style>
