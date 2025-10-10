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
  <v-card outlined min-height="550" style="overflow: hidden">
    <v-row>
      <v-col v-if="matches.savedSearches.length" cols="3">
        <h5 class="mt-3 ml-4">Saved searches</h5>
        <v-list dense style="height: 500px" class="overflow-y-auto" :class="scrollbarTheme">
          <v-list-item
            v-for="savedSearch in matches.savedSearches"
            :key="savedSearch.id"
            v-on:click="$emit('setActiveView', savedSearch)"
            style="font-size: 0.9em"
          >
              {{ savedSearch.name }}
          </v-list-item>
        </v-list>
      </v-col>

      <v-col v-if="matches.timeFilters.length" cols="3">
        <h5 class="mt-3 ml-4">Last time filters</h5>
        <v-list dense style="height: 500px" class="overflow-y-auto" :class="scrollbarTheme">
          <template
            v-for="timeFilter in matches.timeFilters.slice(0, MAX_TIMELINE_ELEMENTS)"
            :key="timeFilter.value"
          >
            <v-list-item
              style="font-size: 0.9em"
              v-on:click="setTimeFilter(timeFilter)"
            >
              <v-list-item-content>
                {{timeFilter.value.split(',')[0]}} - {{  timeFilter.value.split(',')[1]}}
              </v-list-item-content>
            </v-list-item>
          </template>
        </v-list>
      </v-col>
      <v-divider vertical></v-divider>

      <v-col cols="3">
        <div class="d-flex" style="height: 100%">
          <v-divider vertical></v-divider>
          <div class="pl-4 flex-grow-1">
            <h5 class="mt-3">Data types</h5>
            <DataTypesList
              mode="scroll"
            ></DataTypesList>
          </div>
        </div>
      </v-col>

      <v-col v-if="matches.labels.length || matches.tags.length" cols="3">
        <div class="d-flex" style="height: 100%">
          <v-divider vertical></v-divider>
          <div class="pl-5 flex-grow-1">
            <h5 class="mt-3">Tags</h5>
            <TagsList
              mode="scroll"
            ></TagsList>
          </div>
        </div>
      </v-col>
    </v-row>
  </v-card>
</template>

<script>
import { useAppStore } from "@/stores/app"

export default {
  props: ['selectedLabels', 'queryString'],
  data() {
    return {
      appStore: useAppStore(),
    }
  },
  computed: {
    sketch() {
      return this.appStore.sketch
    },
    meta() {
      return this.appStore.meta
    },
    searchHistory() {
      return this.appStore.searchHistory
    },
    tags() {
      return this.appStore.tags
    },
    dataTypes() {
      return this.appStore.dataTypes
    },
    filteredMetaLabels() {
      return this.meta.filter_labels.filter(
        (label) => !label.label.startsWith('__ts_fact')
      );
    },
    all() {
      return {
        fields: this.meta.mappings,
        tags: this.tags,
        labels: this.filteredMetaLabels,
        dataTypes: this.dataTypes,
        savedSearches: this.meta.views,
        timeFilters: this.timeFilters
      }
    },
    timeFilters() {
      return this.appStore.timeFilters;
    },
    scrollbarTheme() {
      return this.$vuetify.theme.dark ? 'dark' : 'light'
    },
    matches() {
      let matches = {}

      if (!this.queryString) {
        return this.all
      }

      matches.fields = this.meta.mappings.filter((field) =>
        field.field.toLowerCase().includes(this.queryString.toLowerCase())
      )
      matches.tags = this.tags.filter((tag) => tag.tag.toLowerCase().includes(this.queryString.toLowerCase()))
      matches.labels = this.filteredMetaLabels.filter((label) =>
        label.label.toLowerCase().includes(this.queryString.toLowerCase())
      )
      matches.dataTypes = this.dataTypes.filter((dataType) =>
        dataType.data_type.toLowerCase().includes(this.queryString.toLowerCase())
      )
      matches.savedSearches = this.meta.views.filter((savedSearch) =>
        savedSearch.name.toLowerCase().includes(this.queryString.toLowerCase())
      )

      if (!Object.values(matches).filter((arr) => arr.length).length) {
        return this.all
      }

      return matches
    },
  },
  methods: {
    searchForDataType(dataType) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = 'data_type:' + '"' + dataType + '"'
      this.$emit('setQueryAndFilter', eventData)
    },
    searchForField(field) {
      let eventData = {}
      let separator = ''
      if (this.queryString !== '') {
        separator = this.queryString + ' '
      }
      if (!this.queryString.includes(' ')) {
        separator = ''
      }
      eventData.doSearch = false
      eventData.queryString = separator + field + ':'
      this.$emit('setQueryAndFilter', eventData)
    },
    setTimeFilter(timeFilter) {
      this.$emit('addChip', timeFilter)
    },
    fetchTimeFilters() {
      this.appStore.updateTimeFilters()
    },
  },
  created: function () {
    this.fetchTimeFilters()
  },
  setup: function() {
    return {
      MAX_TIMELINE_ELEMENTS: 10
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.light::-webkit-scrollbar {
  width: 10px;
}

.light::-webkit-scrollbar-track {
  //background: #e6e6e6;
  //border-left: 1px solid #dadada;
}

.light::-webkit-scrollbar-thumb {
  background: #b0b0b0;
  //border: solid 3px #e6e6e6;
  border-radius: 7px;
}

.light::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

.dark::-webkit-scrollbar {
  width: 10px;
}

.dark::-webkit-scrollbar-track {
  //background: #202020;
  //border-left: 1px solid #2c2c2c;
  //border-right: 1px solid #2c2c2c;
}

.dark::-webkit-scrollbar-thumb {
  background: #3e3e3e;
  //border: solid 3px #202020;
  border-radius: 7px;
}

.dark::-webkit-scrollbar-thumb:hover {
  background: #4e4e4e;
}
</style>
