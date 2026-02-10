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
  <ts-search-guide-card
    :flat="inDialog"
    :show-tags="showTags"
    :show-data-types="showDataTypes"
    :show-saved-searches="showSavedSearches"
  >
    <template v-slot:header>
      <div class="pa-4 pb-0">
        <v-card-title>
          <v-icon large left>mdi-alert-circle-outline</v-icon>
          No Results Found
          <v-spacer></v-spacer>
          <v-btn v-if="inDialog" icon @click="$emit('close-dialog')" title="Close dialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-subtitle class="mt-1">
          <p>
            Your search <code v-if="currentQueryString">'{{ currentQueryString }}'</code>
            <span v-if="filterChips.length"
              >in combination with the selected filter chips
              <code>'{{ filterChips.map((chip) => chip.value).join(', ') }}'</code></span
            >
            did not match any events.
          </p>
          <p v-if="!disableSaveSearch">
            <v-btn small depressed title="Save Search" @click="$emit('save-search-clicked')">
              <v-icon left small>mdi-content-save-outline</v-icon>
              Save search
            </v-btn>
          </p>
          <p>Suggestions:</p>
          <ul>
            <li>Try different keywords<span v-if="filterChips.length"> or filter terms</span>.</li>
            <li>Try more general keywords.</li>
            <li>Try fewer keywords<span v-if="filterChips.length"> or filter terms</span>.</li>
            <li>Try some of the search examples below.</li>
          </ul>
        </v-card-subtitle>
        <v-divider></v-divider>
      </div>
    </template>
  </ts-search-guide-card>
</template>

<script>
import TsSearchGuideCard from './SearchGuideCard.vue'

export default {
  name: 'TsSearchNotFoundCard',
  props: {
    inDialog: {
      type: Boolean,
      default: false,
    },
    currentQueryString: {
      type: String,
      default: '',
    },
    filterChips: {
      type: Array,
      default: () => [],
    },
    disableSaveSearch: {
      type: Boolean,
      default: false,
    },
  },
  components: {
    TsSearchGuideCard,
  },
  computed: {
    showTags() {
      if (!this.$store.state.tags || !this.$store.state.meta.filter_labels) return false
      const filteredLabels = this.$store.state.meta.filter_labels.filter(
        (labelObj) => !labelObj.label.startsWith('__ts_fact')
      )
      return [...this.$store.state.tags, ...filteredLabels].length > 0
    },
    showDataTypes() {
      return this.$store.state.dataTypes.length > 0
    },
    showSavedSearches() {
      return this.$store.state.meta.views.length > 0
    },
  },
}
</script>
