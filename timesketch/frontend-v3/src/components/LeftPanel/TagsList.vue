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
    <v-data-iterator
      :items="allTagsAndLabels"
      v-model:items-per-page="itemsPerPage"
      v-model:page="page"
      :search="search"
    >
      <template v-slot:header>
        <div v-if="showSearch" class="pa-2">
          <v-text-field
            v-model="search"
            clearable
            hide-details
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-magnify"
            label="Search for tags ..."
          ></v-text-field>
        </div>
      </template>
      <template v-slot:default="props">
        <div :style="containerStyles">
          <div
            v-for="item in props.items"
            :key="item.raw.tag || item.raw.label"
            @click="applyFilterChip(item.raw.tag || item.raw.label, item.raw.tag ? 'tag' : '', item.raw.tag ? 'term' : 'label')"
            style="cursor: pointer; font-size: 0.9em"
          >
            <v-row no-gutters class="pa-2 pl-5" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
              <v-icon v-if="item.raw.label === '__ts_star'" size="small" class="mr-2" color="amber">mdi-star</v-icon>
              <v-icon v-if="item.raw.label === '__ts_comment'" size="small" class="mr-2">mdi-comment-multiple-outline</v-icon>
              <v-icon v-if="getQuickTag(item.raw.tag)" size="small" class="mr-2" :color="getQuickTag(item.raw.tag).color">{{ getQuickTag(item.raw.tag).label }}</v-icon>
              <v-icon v-else-if="item.raw.tag" size="small" class="mr-2">mdi-tag</v-icon>

              <span>
                {{ $filters.formatLabelText((item.raw.tag || item.raw.label)) }} (<small><strong>{{  $filters.compactNumber(item.raw.count) }}</strong></small>)
              </span>
            </v-row>
          </div>
        </div>
      </template>
      <template v-slot:footer>
        <div v-if="!isScrollMode && numberOfPages > 1" class="d-flex justify-center pa-2">
          <v-pagination v-model="page" :length="numberOfPages" :total-visible="5" density="compact"></v-pagination>
        </div>
      </template>
    </v-data-iterator>
  </div>
</template>

<script>
import EventBus from "@/event-bus.js";
import { useAppStore } from "@/stores/app";

export default {
  props: {
    mode: {
      type: String,
      default: 'paginate',
      validator: (val) => ['paginate', 'scroll'].includes(val),
    },
    searchThreshold: {
      type: Number,
      default: 10,
    },
    scrollHeight: {
      type: String,
      default: '500px',
    },
    pageSize: {
      type: Number,
      default: 10,
    },
  },
  data: function () {
    return {
      appStore: useAppStore(),
      quickTags: [
        { tag: 'bad', color: 'red', textColor: 'white', label: 'mdi-alert-circle-outline' },
        { tag: 'suspicious', color: 'orange', textColor: 'white', label: 'mdi-help-circle-outline' },
        { tag: 'good', color: 'green', textColor: 'white', label: 'mdi-check-circle-outline' },
      ],
      itemsPerPage: this.pageSize,
      search: '',
      page: 1,
    }
  },
  computed: {
    meta() {
      return this.appStore.meta
    },
    tags() {
      return this.appStore.tags
    },
    labels() {
      return this.meta.filter_labels
    },
    customTags() {
      return this.tags.filter((tag) => !this.getQuickTag(tag.tag))
    },
    assignedQuickTags() {
      return this.tags.filter((tag) => this.getQuickTag(tag.tag))
    },
    allTagsAndLabels() {
      const labelOrder = ['__ts_star', '__ts_comment', 'bad', 'suspicious', 'good']
      return [...this.labels, ...this.assignedQuickTags, ...this.customTags]
        .filter(item => item.tag || item.label)
        .filter(item => !(item.label && item.label.startsWith('__ts_fact')))
        .sort((a, b) => {
          const aLabel = a.tag || a.label
          const bLabel = b.tag || b.label
          const aIsLabel = !!a.label
          const bIsLabel = !!b.label
          if (aIsLabel && !bIsLabel) return -1
          if (!aIsLabel && bIsLabel) return 1
          const aOrder = labelOrder.indexOf(aLabel)
          const bOrder = labelOrder.indexOf(bLabel)
          if (aOrder > -1 && bOrder > -1) return aOrder - bOrder
          if (aOrder > -1) return -1
          if (bOrder > -1) return 1
          return aLabel.localeCompare(bLabel)
        })
    },
    isScrollMode() {
      return this.mode === 'scroll'
    },
    showSearch() {
      return this.allTagsAndLabels.length > this.searchThreshold
    },
    containerStyles() {
      if (this.isScrollMode) {
        return {
          maxHeight: this.scrollHeight,
          overflowY: 'auto',
        }
      }
      return {}
    },
    numberOfPages() {
      if (this.itemsPerPage <= 0) return 1
      return Math.ceil(this.allTagsAndLabels.length / this.itemsPerPage)
    },
  },
  watch: {
    mode: {
      immediate: true,
      handler(newVal) {
        if (newVal === 'scroll') {
          this.itemsPerPage = -1
        } else {
          this.itemsPerPage = this.pageSize
        }
      },
    },
  },
  methods: {
    getQuickTag(tag) {
      return this.quickTags.find((el) => el.tag === tag)
    },
    applyFilterChip(term, termField='', termType='label') {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = '*'
      let chip = {
        field: termField,
        value: term,
        type: termType,
        operator: 'must',
        active: true,
      }
      eventData.chip = chip
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
}
</script>
