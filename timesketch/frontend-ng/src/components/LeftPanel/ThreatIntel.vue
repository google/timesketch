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
    <v-row
      no-gutters
      style="cursor: pointer"
      class="pa-4"
      flat
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span
        ><v-icon left>mdi-shield-search</v-icon> Threat Intelligence (<small
          ><strong>{{ intelligenceData.length }}</strong></small
        >)</span
      >
      <v-spacer></v-spacer>

      <v-btn
        v-if="expanded"
        small
        depressed
        color="primary"
        outlined
        :to="{ name: 'Intelligence', params: { sketchId: sketch.id } }"
        @click.stop=""
      >
        <v-icon small left>mdi-pencil</v-icon>Manage
      </v-btn>
    </v-row>

    <v-expand-transition>
      <div v-show="expanded">
        <v-divider></v-divider>

        <v-tabs grow v-model="tabs">
          <v-tab>
            Indicators (<small> {{ intelligenceData.length }} </small>)
          </v-tab>
          <v-tab>
            Tags (<small>{{ Object.keys(tagInfo).length }} </small>)
          </v-tab>
        </v-tabs>
        <v-tabs-items v-model="tabs">
          <v-tab-item :transition="false">
            <v-data-table dense :headers="indicatorHeaders" :items="intelligenceData" :items-per-page="10">
              <template v-slot:item.ioc="{ item }">
                <span v-if="item.type === 'hash_sha256'" :title="item.ioc">
                  <span>{{ item.ioc.substring(0, 8) }}...{{ item.ioc.substring(item.ioc.length - 8) }}</span>
                </span>
                <span v-else>
                  {{ item.ioc }}
                </span>
              </template>

              <template v-slot:item.type="{ item }">
                <small>{{ item.type }}</small>
              </template>

              <template v-slot:item.actions="{ item }">
                <v-btn icon small @click="generateSearchQuery(item.ioc)">
                  <v-icon small>mdi-magnify</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-tab-item>
          <v-tab-item :transition="false">
            <v-data-table dense :headers="tagHeaders" :items="Object.values(tagInfo)" :items-per-page="10">
              <template v-slot:item.tag="{ item }">
                <v-chip x-small @click="searchForIOC(item)">{{ item.tag.name }}</v-chip>
              </template>
              <template v-slot:item.iocs="{ item }">
                <small :title="item.iocs">{{ item.iocs.length }}</small>
              </template>
              <template v-slot:item.weight="{ item }">
                <small>{{ item.tag.weight }}</small>
              </template>
              <template v-slot:item.actions="{ item }">
                <v-btn icon small @click="searchForIOC(item)">
                  <v-icon small>mdi-magnify</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-tab-item>
        </v-tabs-items>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import _ from 'lodash'
import ApiClient from '../../utils/RestApiClient'
import EventBus from '../../main'

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
      expanded: false,
      tagInfo: {},
      tagMetadata: {},
      tabs: null,
      indicatorHeaders: [
        { text: 'Indicator', value: 'ioc', align: 'start' },
        { text: 'Type', value: 'type' },
        { value: 'actions' },
      ],
      tagHeaders: [
        { text: 'Tag', value: 'tag', align: 'start' },
        { text: 'Indicators', value: 'iocs' },
        { text: 'Weight', value: 'weight' },
        { value: 'actions' },
      ],
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
    loadSketchAttributes() {
      // buildTagInfo depends on tagMetadata to be present.
      ApiClient.getTagMetadata().then((response) => {
        this.tagMetadata = response.data
        this.buildTagInfo()
      })
    },
    buildTagInfo() {
      // We need tagMetadata to be embedded in the list below as it is used
      // for sorting in the table.
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
              count: 0,
              iocs: [],
              tag: this.enrichTag(tag),
            }
          }
          this.tagInfo[tagKey].count++
          this.tagInfo[tagKey].iocs.push(ioc.ioc)
        }
      }
    },
    enrichTag(tag) {
      if (typeof tag === 'object') {
        return tag
      } else {
        let tagInfo = { name: tag }
        if (this.tagMetadata[tag]) {
          return _.extend(tagInfo, this.tagMetadata[tag])
        } else {
          for (var regex in this.tagMetadata['regexes']) {
            if (tag.match(regex)) {
              return _.extend(tagInfo, this.tagMetadata['regexes'][regex])
            }
          }
          return _.extend(tagInfo, this.tagMetadata.default)
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
      let opensearchQuery = tag.iocs.map((v) => `"${v}"`).reduce((a, b) => `${a} OR ${b}`)
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = opensearchQuery
      eventData.queryFilter = defaultQueryFilter()
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
  mounted() {
    this.loadSketchAttributes()
  },
}
</script>
