<!--
Copyright 2026 Google Inc. All rights reserved.

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
    :search-mode="searchMode"
  >
    <template v-slot:header>
      <div class="pa-4 pb-0">
        <v-card-title>
          <v-icon large left color="error">mdi-alert-circle-outline</v-icon>
          Search Failed
          <v-spacer></v-spacer>
        </v-card-title>
        <v-card-subtitle class="mt-1">
          <p>
            <b>{{ errorText }}</b>
          </p>
          <p>Suggestions:</p>
          <ul v-if="searchMode === 'wildcard'">
            <li>Ensure search terms contain wildcard characters (e.g. <code>*searchterm*</code>).</li>
            <li>Do not escape special characters with backslashes. Matches are literal.</li>
            <li>Encase terms containing <code>:</code> (like URLs, paths, or MACs) in double-quotes, e.g. <code>"*count: 1*"</code>.</li>
            <li>Check for field typos: Ensure that target fields (e.g. <code>message:</code>) are spelled correctly and support wildcard searches.</li>
            <li>Ensure boolean operators (<code>AND</code>, <code>OR</code>, <code>NOT</code>) are capitalized and correctly positioned.</li>
            <li>Try some of the wildcard search examples below.</li>
          </ul>
          <ul v-else>
            <li>Avoid leading wildcards like <code>*searchterm*</code></li>
            <li>Try searching a specific field like <code>message:*searchterm*</code></li>
            <li>Escape <a href="https://docs.opensearch.org/latest/query-dsl/full-text/query-string/#reserved-characters" target="_blank">reserved characters</a> in your query.</li>
            <li>Try a shorter time range.</li>
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
  name: 'TsSearchErrorCard',
  props: {
    inDialog: {
      type: Boolean,
      default: false,
    },
    errorText: {
      type: String,
      default: 'An unknown error occurred.',
    },
    searchMode: {
      type: String,
      default: 'query_string',
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
