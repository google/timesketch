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
  <v-row>
    <v-col cols="4">
      <v-sheet class="pa-4">
        <strong>Fields</strong>
        <v-list dense style="max-height: 600px" class="overflow-y-auto" :class="scrollbarTheme">
          <v-list-item v-for="field in matches.fields" :key="field.field" v-on:click="searchForField(field.field)">
            <v-list-item-content>
              <v-list-item-title>{{ field.field }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-sheet>
    </v-col>

    <v-col cols="4">
      <v-sheet class="pa-4">
        <strong>Data Types</strong>
        <v-list dense style="max-height: 600px" class="overflow-y-auto" :class="scrollbarTheme">
          <v-list-item
            v-for="dataType in matches.dataTypes"
            :key="dataType.data_type"
            v-on:click="searchForDataType(dataType.data_type)"
          >
            <v-list-item-content>
              <v-list-item-title>
                <span>
                  {{ dataType.data_type }} <strong>({{ dataType.count | compactNumber }})</strong>
                </span>
              </v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-sheet>
    </v-col>
  </v-row>
</template>

<script>
//import TsViewListCompact from '../Common/ViewListCompact'

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
  components: {
    //TsViewListCompact,
  },
  props: ['selectedLabels', 'queryString'],
  computed: {
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
    all() {
      return {
        fields: this.meta.mappings,
        tags: this.tags,
        labels: this.meta.filter_labels,
        dataTypes: this.dataTypes,
        savedSearches: this.meta.views,
      }
    },
    scrollbarTheme() {
      return this.$vuetify.theme.dark ? 'dark' : 'light'
    },
    matches() {
      let matches = {}

      if (!this.queryString) {
        return this.all
      }

      matches['fields'] = this.meta.mappings.filter((field) =>
        field.field.toLowerCase().includes(this.queryString.toLowerCase())
      )
      matches['tags'] = this.tags.filter((tag) => tag.tag.toLowerCase().includes(this.queryString.toLowerCase()))
      matches['labels'] = this.meta.filter_labels.filter((label) =>
        label.label.toLowerCase().includes(this.queryString.toLowerCase())
      )
      matches['dataTypes'] = this.dataTypes.filter((dataType) =>
        dataType.data_type.toLowerCase().includes(this.queryString.toLowerCase())
      )
      matches['savedSearches'] = this.meta.views.filter((savedSearch) =>
        savedSearch.name.toLowerCase().includes(this.queryString.toLowerCase())
      )

      if (!Object.values(matches).filter((arr) => arr.length).length) {
        return this.all
      }

      return matches
    },
  },
  methods: {
    searchForLabel(label) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = '*'
      eventData.queryFilter = defaultQueryFilter()
      let chip = {
        field: '',
        value: label,
        type: 'label',
        operator: 'must',
        active: true,
      }
      eventData.queryFilter.chips.push(chip)
      this.$emit('setQueryAndFilter', eventData)
    },
    searchForTag(tag) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = 'tag:' + tag
      eventData.queryFilter = defaultQueryFilter()
      this.$emit('setQueryAndFilter', eventData)
    },
    searchForDataType(dataType) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = 'data_type:' + '"' + dataType + '"'
      eventData.queryFilter = defaultQueryFilter()
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
      eventData.queryFilter = defaultQueryFilter()
      this.$emit('setQueryAndFilter', eventData)
    },
  },
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
