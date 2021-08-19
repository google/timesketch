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
  <div style="max-height:600px;border-top:1px solid var(--table-cell-border-color);overflow: hidden;">
    <div class="columns is-gapless" v-if="Object.keys(matches).length">
      <div
        class="column"
        style="max-width:50%;overflow:auto;overflow-x: hidden;max-height:600px;"
        v-if="matches.fields.length"
      >
        <div style="padding:20px;">
          <div style="padding-bottom:10px;"><strong>Fields</strong></div>
          <div
            v-for="field in matches.fields"
            :key="field.field"
            v-on:click="searchForField(field.field)"
            class="list-item"
            style="cursor:pointer;padding:5px 0 5px 0;"
          >
            <span style="margin-right:5px;">{{ field.field }}</span>
          </div>
        </div>
      </div>

      <div
        class="column"
        v-if="matches.dataTypes.length"
        style="border-left:1px solid var(--table-cell-border-color);max-width:50%;overflow:auto;overflow-x: hidden;max-height:600px;"
      >
        <div style="padding:20px;">
          <div style="padding-bottom:10px;"><strong>Data Types</strong></div>
          <div
            v-for="dataType in matches.dataTypes"
            :key="dataType.data_type"
            v-on:click="searchForDataType(dataType.data_type)"
            class="list-item"
            style="cursor:pointer;padding:5px 0 5px 0;"
          >
            <span style="margin-right:5px;">{{ dataType.data_type }}</span>
            <strong style="opacity:0.9;">({{ dataType.count | compactNumber }})</strong>
          </div>
        </div>
      </div>

      <div
        v-if="matches.tags.length || matches.labels.length"
        class="column"
        style="border-left:1px solid var(--table-cell-border-color);max-width:50%;overflow:auto;overflow-x: hidden;max-height:600px;"
      >
        <div style="padding:20px;">
          <div style="padding-bottom:10px;"><strong>Tags</strong></div>
          <div
            v-for="label in matches.labels"
            :key="label.label"
            v-on:click="searchForLabel(label.label)"
            class="list-item"
            style="cursor:pointer;padding:5px 0 5px 0;"
          >
            <span v-if="label.label === '__ts_star'">
              <span style="margin-right:5px;" class="icon is-small"
                ><i
                  class="fas fa-star"
                  style="color:#ffe300;-webkit-text-stroke-width: 1px;-webkit-text-stroke-color: silver;"
                ></i
              ></span>
              Starred
            </span>
            <span v-else-if="label.label === '__ts_comment'">
              <span style="margin-right:5px;" class="icon is-small"><i class="fas fa-comment"></i></span>
              Commented
            </span>
            <span v-else style="margin-right:5px;">{{ label.label }}</span>
            <strong style="opacity:0.9;">({{ label.count | compactNumber }})</strong>
          </div>
          <div
            v-for="tag in matches.tags"
            :key="tag.tag"
            v-on:click="searchForTag(tag.tag)"
            class="list-item"
            style="cursor:pointer;padding:5px 0 5px 0;"
          >
            <span style="margin-right:5px;">{{ tag.tag }}</span>
            <strong style="opacity:0.9;">({{ tag.count | compactNumber }})</strong>
          </div>
        </div>
      </div>

      <div
        class="column"
        style="border-left:1px solid var(--table-cell-border-color);max-width:50%;overflow:auto;overflow-x: hidden;max-height:600px;"
        v-if="matches.savedSearches.length"
      >
        <div style="padding:20px;">
          <div style="padding-bottom:10px;"><strong>Saved Searches</strong></div>
          <ts-view-list-compact
            :views="matches.savedSearches"
            @setActiveView="$emit('setActiveView', $event)"
          ></ts-view-list-compact>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TsViewListCompact from '../Common/ViewListCompact'

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
    TsViewListCompact,
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
    matches() {
      let matches = {}

      if (!this.queryString) {
        return this.all
      }

      matches['fields'] = this.meta.mappings.filter(field =>
        field.field.toLowerCase().includes(this.queryString.toLowerCase())
      )
      matches['tags'] = this.tags.filter(tag => tag.tag.toLowerCase().includes(this.queryString.toLowerCase()))
      matches['labels'] = this.meta.filter_labels.filter(label =>
        label.label.toLowerCase().includes(this.queryString.toLowerCase())
      )
      matches['dataTypes'] = this.dataTypes.filter(dataType =>
        dataType.data_type.toLowerCase().includes(this.queryString.toLowerCase())
      )
      matches['savedSearches'] = this.meta.views.filter(savedSearch =>
        savedSearch.name.toLowerCase().includes(this.queryString.toLowerCase())
      )

      if (!Object.values(matches).filter(arr => arr.length).length) {
        return this.all
      }

      return matches
    },
  },
  beforeDestroy: function() {
    window.removeEventListener('click', this.close)
  },
  created: function() {
    window.addEventListener('click', this.close)
  },
  methods: {
    close(e) {
      if (!this.$el.contains(e.target)) {
        this.$emit('close', e.target)
      }
    },
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
.list-item:hover {
  background-color: var(--table-row-hover-background-color);
}
</style>
