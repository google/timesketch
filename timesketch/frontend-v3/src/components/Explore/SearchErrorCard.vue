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
          <ul>
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
import { useAppStore } from "@/stores/app";

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
  },
  components: {
    TsSearchGuideCard,
  },
  data() {
    return {
      appStore: useAppStore(),
    }
  },
  computed: {
    showTags() {
      if (!this.appStore.tags || !this.appStore.meta.filter_labels) return false
      const filteredLabels = this.appStore.meta.filter_labels.filter(
        (labelObj) => !labelObj.label.startsWith('__ts_fact')
      )
      return [...this.appStore.tags, ...filteredLabels].length > 0
    },
    showDataTypes() {
      return this.appStore.dataTypes.length > 0
    },
    showSavedSearches() {
      return this.appStore.meta.views.length > 0
    },
  },
}
</script>
