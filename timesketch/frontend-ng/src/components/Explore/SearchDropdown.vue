<!--
Copyright 2021 Google Inc. All rights reserved.

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
    <v-row class="pa-4">
      <v-col v-if="all.fields && all.fields.length" cols="12" sm="6" md="4" lg="3" xl="2">
        <h5 class="mb-2">Fields</h5>
        <v-list dense style="height: 500px" class="overflow-y-auto" :class="scrollbarTheme">
          <template v-if="matches.fields && matches.fields.length">
            <v-list-item
              v-for="field in matches.fields"
              :key="field.field"
              v-on:click="searchForField(field.field)"
              style="font-size: 0.9em"
            >
              <v-list-item-content>
                <span>
                  {{ field.field }}
                  <span class="text--secondary font-weight-light" style="font-size: 0.8em">
                    ({{ field.type }})
                  </span>
                </span>
              </v-list-item-content>
            </v-list-item>
          </template>
          <v-list-item v-else>
            <v-list-item-content class="text--secondary font-italic font-weight-light">
              No matching fields
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-col>

      <v-col v-if="all.savedSearches && all.savedSearches.length" cols="12" sm="6" md="4" lg="3" xl="2">
        <h5 class="mb-2">Saved searches</h5>
        <v-list dense style="height: 500px" class="overflow-y-auto" :class="scrollbarTheme">
          <template v-if="matches.savedSearches && matches.savedSearches.length">
            <v-list-item
              v-for="savedSearch in matches.savedSearches"
              :key="savedSearch.id"
              v-on:click="$emit('setActiveView', savedSearch)"
              style="font-size: 0.9em"
            >
              <v-list-item-content>
                {{ savedSearch.name }}
              </v-list-item-content>
            </v-list-item>
          </template>
          <v-list-item v-else>
            <v-list-item-content class="text--secondary font-italic font-weight-light">
              No matching saved searches
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-col>

      <v-col v-if="all.timeFilters && all.timeFilters.length" cols="12" sm="6" md="4" lg="3" xl="2">
        <h5 class="mb-2">Last time filters</h5>
        <v-list dense style="height: 500px" class="overflow-y-auto" :class="scrollbarTheme">
          <template v-if="matches.timeFilters && matches.timeFilters.length">
            <v-list-item
              style="font-size: 0.9em"
              v-for="timeFilter in matches.timeFilters.slice(0, MAX_TIMELINE_ELEMENTS)"
              :key="timeFilter.value"
              v-on:click="setTimeFilter(timeFilter)"
            >
              <v-list-item-content>
                {{timeFilter.value.split(',')[0]}} - {{  timeFilter.value.split(',')[1]}}
              </v-list-item-content>
            </v-list-item>
          </template>
          <v-list-item v-else>
            <v-list-item-content class="text--secondary font-italic font-weight-light">
              No matching time filters
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-col>

      <v-col v-if="all.dataTypes && all.dataTypes.length" cols="12" sm="6" md="4" lg="3" xl="2">
        <h5 class="mb-2">Data types</h5>
        <v-list dense style="height: 500px" class="overflow-y-auto" :class="scrollbarTheme">
          <template v-if="matches.dataTypes && matches.dataTypes.length">
            <v-list-item
              v-for="dataType in matches.dataTypes"
              :key="dataType.data_type"
              v-on:click="searchForDataType(dataType.data_type)"
              style="font-size: 0.9em"
            >
              <v-list-item-content>
                <span
                  >{{ dataType.data_type }}
                  <span class="font-weight-bold" style="font-size: 0.8em"
                    >({{ dataType.count | compactNumber }})</span
                  ></span
                >
              </v-list-item-content>
            </v-list-item>
          </template>
          <v-list-item v-else>
            <v-list-item-content class="text--secondary font-italic font-weight-light">
              No matching data types
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-col>

      <v-col v-if="(all.labels && all.labels.length) || (all.tags && all.tags.length)" cols="12" sm="6" md="4" lg="3" xl="2">
        <h5 class="mb-2">Tags</h5>
        <ts-tags-list :search-query="matches === all ? '' : activeToken"></ts-tags-list>
      </v-col>
    </v-row>
  </v-card>
</template>

<script>
import TsTagsList from '../LeftPanel/TagsList.vue'

export default {
  components: {
    TsTagsList,
  },
  props: ['selectedLabels', 'queryString'],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    searchHistory() {
      return this.$store.state.searchHistory
    },
    tags() {
      return this.$store.state.tags
    },
    dataTypes() {
      return this.$store.state.dataTypes
    },
    filteredMetaLabels() {
      if (!this.meta || !this.meta.filter_labels) {
        return []
      }
      return this.meta.filter_labels.filter(
        (label) => !label.label.startsWith('__ts_fact')
      );
    },
    all() {
      return {
        fields: this.meta.mappings || [],
        tags: this.tags || [],
        labels: this.filteredMetaLabels || [],
        dataTypes: this.dataTypes || [],
        savedSearches: this.meta.views || [],
        timeFilters: this.timeFilters || []
      }
    },
    timeFilters() {
      return this.$store.state.timeFilters;
    },
    scrollbarTheme() {
      return this.$vuetify.theme.dark ? 'dark' : 'light'
    },
    activeToken() {
      if (!this.queryString) {
        return ''
      }

      // Disable autocomplete if the user is typing inside an open quote
      const quoteCount = (this.queryString.match(/"/g) || []).length
      if (quoteCount % 2 !== 0) {
        return ''
      }

      const parts = this.queryString.split(/\s+/)
      if (!parts.length) {
        return ''
      }
      const lastToken = parts[parts.length - 1]

      // If the last token contains a colon, we are typing a field value (e.g. 'field:val' or 'field:')
      // We don't want to autocomplete field names/tags in this state.
      if (lastToken.includes(':')) {
        return ''
      }

      // If the last token is a boolean operator, reset to show all suggestions.
      const upperToken = lastToken.toUpperCase()
      if (upperToken === 'AND' || upperToken === 'OR' || upperToken === 'NOT') {
        return ''
      }

      return lastToken
    },
    matches() {
      let matches = {}

      if (!this.activeToken) {
        return this.all
      }

      const mappings = this.meta.mappings || []
      matches.fields = mappings.filter((field) =>
        field.field.toLowerCase().includes(this.activeToken.toLowerCase())
      )
      const tags = this.tags || []
      matches.tags = tags.filter((tag) => tag.tag.toLowerCase().includes(this.activeToken.toLowerCase()))

      const labels = this.filteredMetaLabels || []
      matches.labels = labels.filter((label) =>
        label.label.toLowerCase().includes(this.activeToken.toLowerCase())
      )

      const dataTypes = this.dataTypes || []
      matches.dataTypes = dataTypes.filter((dataType) =>
        dataType.data_type.toLowerCase().includes(this.activeToken.toLowerCase())
      )

      const views = this.meta.views || []
      matches.savedSearches = views.filter((savedSearch) =>
        savedSearch.name.toLowerCase().includes(this.activeToken.toLowerCase())
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
      const parts = this.queryString.split(/\s+/)
      parts.pop() // Remove the partial token
      parts.push('data_type:' + '"' + dataType + '"')
      eventData.doSearch = true
      eventData.queryString = parts.join(' ')
      this.$emit('setQueryAndFilter', eventData)
    },
    searchForField(field) {
      let eventData = {}
      const parts = this.queryString.split(/\s+/)
      parts.pop() // Remove the partial token
      parts.push(field + ':') // Add the completed field suggestion
      eventData.doSearch = false
      eventData.queryString = parts.join(' ')
      this.$emit('setQueryAndFilter', eventData)
    },
    setTimeFilter(timeFilter) {
      this.$emit('addChip', timeFilter)
    },
    fetchTimeFilters() {
      this.$store.dispatch('updateTimeFilters')
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
