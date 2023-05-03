<!--
Copyright 2023 Google Inc. All rights reserved.

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
    <ts-indicator-dialog
      :dialog.sync="indicatorDialog"
      :index="currentIndex"
      :tag-info="tagInfo"
      @open-dialog="indicatorDialog = true"
      @close-dialog="
        indicatorDialog = false
        currentIndex = -1
      "
      @save="
        saveIntelligence($event)
        indicatorDialog = false
      "
    >
    </ts-indicator-dialog>

    <v-container fluid>
      <v-btn class="mt-n1 ml-3" text color="primary" @click="addIndicator">
        <v-icon left>mdi-plus</v-icon>
        Add Indicator
      </v-btn>

      <v-card outlined class="mt-3 mx-3">
        <v-data-table
          :headers="headers"
          :items="intelligenceData"
          :footer-props="{ 'items-per-page-options': [10, 40, 80, 100, 200, 500], 'show-current-page': true }"
          :items-per-page="40"
        >
          <template v-slot:item.search="{ item }">
            <v-btn icon small @click="generateSearchQuery(item.ioc)">
              <v-icon small>mdi-magnify</v-icon>
            </v-btn>
          </template>

          <template v-slot:item.externalURI="{ item }">
            <v-icon v-if="item.externalURI" x-small>mdi-open-in-new</v-icon>
            <a
              style="text-decoration: none"
              v-if="getValidUrl(item.externalURI)"
              :href="getValidUrl(item.externalURI)"
              target="_blank"
            >
              {{ getValidUrl(item.externalURI).host }}</a
            >
          </template>
          <template v-slot:item.tags="{ item }">
            <v-chip-group>
              <v-chip small v-for="tag in item.tags" :key="tag" @click="searchForIOC(tag)">
                {{ tag }}
              </v-chip>
            </v-chip-group>
          </template>

          <template v-slot:item.actions="{ item }">
            <v-btn small icon @click="editIndicator(item.index)">
              <v-icon small>mdi-pencil</v-icon>
            </v-btn>
            <v-btn small icon @click="deleteIndicator(item.index)">
              <v-icon small>mdi-trash-can-outline</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card>
    </v-container>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import EventBus from '../main'
import TsIndicatorDialog from '../components/ThreatIntel/IndicatorDialog'

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
  components: {
    TsIndicatorDialog,
  },
  data: function () {
    return {
      headers: [
        { text: '', value: 'search', align: 'start' },
        { text: 'Indicator data', value: 'ioc' },
        { text: 'Indicator type', value: 'type' },
        { text: 'Tags', value: 'tags' },
        { text: 'External reference', value: 'externalURI' },
        { text: '', value: 'actions' },
      ],
      tagInfo: {},
      indicatorDialog: false,
      currentIndex: -1,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    intelligenceAttribute() {
      if (this.meta.attributes.intelligence === undefined) {
        return { ontology: 'intelligence', value: { data: [] }, name: 'intelligence' }
      }
      return this.meta.attributes.intelligence
    },
    intelligenceData() {
      return this.intelligenceAttribute.value.data.map((x, idx) => ({ ...x, index: idx }))
    },
  },
  methods: {
    addIndicator() {
      this.indicatorDialog = true
    },
    deleteIndicator(index) {
      if (confirm('Delete indicator?')) {
        this.intelligenceAttribute.value.data.splice(index, 1)
        ApiClient.addSketchAttribute(this.sketch.id, 'intelligence', this.intelligenceAttribute.value, 'intelligence')
          .then(() => {
            this.successSnackBar('Indicator deleted')
            this.buildTagInfo()
          })
          .catch((e) => {
            this.errorSnackBar('Failed to save indicator')
            console.error(e)
          })
      }
    },
    editIndicator(index) {
      this.currentIndex = index
      this.indicatorDialog = true
    },
    getValidUrl(urlString) {
      if (urlString === undefined || urlString === null || urlString === '') {
        return false
      }
      if (urlString.startsWith('http')) {
        return new URL(urlString)
      } else if (urlString.includes('/')) {
        return new URL('http://' + urlString)
      } else {
        return false
      }
    },
    buildTagInfo() {
      this.tagInfo = {}
      for (var ioc of this.intelligenceData) {
        for (var tag of ioc.tags) {
          // deal with the case when tag is an object that is already enriched.
          var tagKey = null
          if (typeof tag === 'object') {
            tagKey = tag.name
          } else {
            tagKey = tag
          }
          if (!this.tagInfo[tagKey]) {
            this.tagInfo[tagKey] = {
              iocs: [],
            }
          }
          this.tagInfo[tagKey].iocs.push(ioc.ioc)
        }
      }
    },
    generateSearchQuery(value, field) {
      let query = `"${value}"`
      // Escape special OpenSearch characters: \, [space]
      query = query.replace(/[\\\s]/g, '\\$&')
      if (field !== undefined) {
        query = `${field}:${query}`
      }
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = query
      eventData.queryFilter = defaultQueryFilter()
      EventBus.$emit('setQueryAndFilter', eventData)
    },
    searchForIOC(tag) {
      let tagDetails = this.tagInfo[tag] || {}
      let opensearchQuery = tagDetails.iocs.map((v) => `"${v}"`).reduce((a, b) => `${a} OR ${b}`)
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = opensearchQuery
      eventData.queryFilter = defaultQueryFilter()
      EventBus.$emit('setQueryAndFilter', eventData)
    },
    saveIntelligence(indicator) {
      // If this is a new indicator add it to indicator array.
      if (this.currentIndex < 0) {
        this.intelligenceAttribute.value.data.push(indicator)
      }
      ApiClient.addSketchAttribute(this.sketch.id, 'intelligence', this.intelligenceAttribute.value, 'intelligence')
        .then(() => {
          this.successSnackBar('Indicator saved')
          this.buildTagInfo()
        })
        .catch((e) => {
          this.errorSnackBar('Failed to save indicator')
          console.error(e)
        })
    },
    showIndicatorDialog() {
      this.indicatorDialog = true
    },
  },
  mounted() {
    EventBus.$on('addIndicator', this.showIndicatorDialog)
    this.buildTagInfo()
  },
  beforeDestroy() {
    EventBus.$off('addIndicator')
  },
}
</script>
