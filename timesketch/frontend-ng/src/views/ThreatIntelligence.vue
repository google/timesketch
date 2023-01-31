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
  <v-container fluid>
    <v-btn class="mt-n1" text color="primary" style="cursor: pointer"
      ><v-icon left>mdi-plus</v-icon> Add Indicator</v-btn
    >
    <v-card outlined class="mt-3 mx-3">
      <v-data-table :headers="headers" :items="intelligenceData" :items-per-page="40">
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
      </v-data-table>
    </v-card>
  </v-container>
</template>

<script>
import EventBus from '../main'

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
      headers: [
        { text: 'Indicator data', value: 'ioc', align: 'start' },
        { text: 'Indicator type', value: 'type' },
        { text: 'Tags', value: 'tags' },
        { text: 'External reference', value: 'externalURI' },
      ],
      tagInfo: {},
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
      return this.intelligenceAttribute.value.data
    },
  },
  methods: {
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
          // deal with the case when tag is an object that is alread enriched.
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
    searchForIOC(tag) {
      let tagDetails = this.tagInfo[tag] || {}
      let opensearchQuery = tagDetails.iocs.map((v) => `"${v}"`).reduce((a, b) => `${a} OR ${b}`)
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = opensearchQuery
      eventData.queryFilter = defaultQueryFilter()
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
  mounted() {
    this.buildTagInfo()
  },
}
</script>
