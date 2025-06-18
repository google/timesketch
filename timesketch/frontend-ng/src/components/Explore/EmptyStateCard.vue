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
  <v-card :outlined="!inDialog" :class="{ 'ma-4': !inDialog }">
    <!-- Header Section -->
    <div v-if="displayMode === 'InfoCard'" class="pa-4 pb-0">
      <v-card-title>
        <v-icon large left>mdi-file-search-outline</v-icon>
        Search Examples and Query Guide
        <v-spacer></v-spacer>
        <v-btn v-if="inDialog" icon @click="$emit('close-dialog')" title="Close dialog">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-subtitle class="mt-1"> Find below some examples on how to explore your data. </v-card-subtitle>
      <v-divider></v-divider>
    </div>
    <div v-if="displayMode === 'EmptyState'" class="pa-4 pb-0">
      <v-card-title>
        <v-icon large left>mdi-file-search-outline</v-icon>
        Start Exploring
        <v-spacer></v-spacer>
        <v-btn v-if="inDialog" icon @click="$emit('close-dialog')" title="Close dialog">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-subtitle class="mt-1"> Find below some examples on how to explore your data. </v-card-subtitle>
      <v-divider></v-divider>
    </div>
    <div v-if="displayMode === 'NotFound'" class="pa-4 pb-0">
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

    <!-- Scrollable Content Section -->
    <v-card-text>
      <v-row no-gutters>
        <v-col style="min-width: 250px; flex-basis: 25%">
          <div class="pa-2">
            <v-simple-table>
              <template v-slot:default>
                <thead>
                  <tr>
                    <th class="text-left">Description</th>
                    <th class="text-left">Example Query</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Search for all events</td>
                    <td>
                      <a href="#" @click.prevent="emitSetQueryAndFilter('*')">
                        <code>*</code>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <td>Search a word in the message field</td>
                    <td>
                      <a href="#" @click.prevent="emitSetQueryAndFilter('message:error')">
                        <code>message:"error"</code>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <td>Search filenames ending with <code>.exe</code></td>
                    <td>
                      <a href="#" @click.prevent="emitSetQueryAndFilter('filename:*.exe')">
                        <code>filename:*.exe</code>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      Search on the
                      <a href="https://docs.opensearch.org/docs/2.19/field-types/supported-field-types/keyword/"
                        >keyword field type</a
                      ><br />(exact matches & substring search)
                    </td>
                    <td>
                      <a href="#" @click.prevent="emitSetQueryAndFilter('filename.keyword:malicious.exe')">
                        <code>filename.keyword:malicious.exe</code> </a
                      ><br />
                      <a href="#" @click.prevent="emitSetQueryAndFilter('message.keyword:*System32*')">
                        <code>message.keyword:*System32*</code>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <td>Search using regex (between <code>//</code>)</td>
                    <td>
                      <a
                        href="#"
                        @click.prevent="emitSetQueryAndFilter('url.keyword:/.*\\/sketch\\/[1-100]\\/.*/')"
                      >
                        <code>url.keyword:/.*\/sketch\/[1-100]\/.*/</code>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <td>Combine searches with AND, OR, NOT</td>
                    <td>
                      <a
                        href="#"
                        @click.prevent="emitSetQueryAndFilter('event_identifier:(4624 OR 4625) AND LogonType:3')"
                      >
                        <code>event_identifier:(4624 OR 4625) AND NOT LogonType:3</code>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <td>Search events that have an url field</td>
                    <td>
                      <a href="#" @click.prevent="emitSetQueryAndFilter('_exists_:url')"> <code>_exists_:url</code> </a
                      ><br />
                      <a href="#" @click.prevent="emitSetQueryAndFilter('url:*')">
                        <code>url:*</code>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <td>Search for a range of numbers</td>
                    <td>
                      <a
                        href="#"
                        @click.prevent="
                          emitSetQueryAndFilter('http_status_code:[200 TO 204] AND bytes_transferred:>10000')
                        "
                      >
                        <code>status_code:[200 TO 204] AND transferred:>10000</code>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <td>Filter by a specific date/time range (UTC)</td>
                    <td>
                      <a
                        href="#"
                        @click.prevent="emitSetQueryAndFilter(`datetime:[${firstOfCurrentMonth} TO ${nowDateTimeUTC}]`)"
                      >
                        <code>datetime:[{{ firstOfCurrentMonth }} TO {{ nowDateTimeUTC }}]</code>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <td>Filter for events before or after a date (UTC)</td>
                      <td>
                      <a href="#" @click.prevent="emitSetQueryAndFilter(`datetime:[${firstOfCurrentMonth} TO *]`)">
                        <code>datetime:[{{ firstOfCurrentMonth }} TO *]</code> </a
                      ><br />
                      <a href="#" @click.prevent="emitSetQueryAndFilter(`datetime:[* TO ${firstOfCurrentMonth}]`)">
                        <code>datetime:[* TO {{ firstOfCurrentMonth }}]</code>
                      </a>
                    </td>
                  </tr>
                </tbody>
              </template>
            </v-simple-table>
          </div>
        </v-col>

        <!-- Dynamically load Tags, DataTypes and SavedSearches Lists -->
        <v-col v-if="showTagsList" style="border-left: 1px solid rgba(0, 0, 0, 0.12)">
          <div class="pa-4">
            <h5><v-icon left>mdi-tag-multiple-outline</v-icon> Tags</h5>
            <ts-tags-list></ts-tags-list>
          </div>
        </v-col>
        <v-col v-if="showDataTypesList" style="border-left: 1px solid rgba(0, 0, 0, 0.12)">
          <div class="pa-4">
            <h5><v-icon left>mdi-database-outline</v-icon> Data Types</h5>
            <ts-data-types-list></ts-data-types-list>
          </div>
        </v-col>
        <v-col v-if="showSavedSearchesList" style="border-left: 1px solid rgba(0, 0, 0, 0.12)">
          <div class="pa-4">
            <h5><v-icon left>mdi-content-save-outline</v-icon> Saved Searches</h5>
            <ts-saved-searches-list></ts-saved-searches-list>
          </div>
        </v-col>
      </v-row>
    </v-card-text>

    <!-- Actions Section -->
    <v-divider></v-divider>
    <v-card-actions>
      <v-btn text color="primary" href="https://timesketch.org/guides/user/search-query-guide/" target="_blank">
        Full Search Guide
        <v-icon right>mdi-open-in-new</v-icon>
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import EventBus from '../../event-bus.js'

import TsTagsList from '../LeftPanel/TagsList.vue'
import TsDataTypesList from '../LeftPanel/DataTypesList.vue'
import TsSavedSearchesList from '../LeftPanel/SavedSearchesList.vue'

export default {
  name: 'EmptyStateCard',
  props: {
    inDialog: {
      type: Boolean,
      default: false,
    },
    displayMode: {
      type: String,
      required: true,
      validator: function (value) {
        return ['EmptyState', 'NotFound', 'InfoCard'].indexOf(value) !== -1
      },
      default: 'EmptyState',
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
    TsTagsList,
    TsDataTypesList,
    TsSavedSearchesList,
  },
  computed: {
    isInfoCard() {
      return this.displayMode === 'InfoCard'
    },
    showTagsList() {
      if ([...this.$store.state.tags, ...this.$store.state.meta.filter_labels].length > 0 && !this.isInfoCard) {
        return true
      }
      return false
    },
    showDataTypesList() {
      if (this.$store.state.dataTypes.length > 0 && !this.isInfoCard) {
        return true
      }
      return false
    },
    showSavedSearchesList() {
      if (this.$store.state.meta.views.length > 0 && !this.isInfoCard) {
        return true
      }
      return false
    },
    firstOfCurrentMonth() {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      return `${year}-${month}-01`
    },
    nowDateTimeUTC() {
      const now = new Date()
      return now.toISOString().slice(0, 19)
    },
  },
  methods: {
    emitSetQueryAndFilter(queryString) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = queryString
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
}
</script>

<style scoped></style>
