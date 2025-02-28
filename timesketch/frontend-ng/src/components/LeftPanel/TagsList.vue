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
    <div>
      <v-data-iterator
          :items="allTagsAndLabels"
          :items-per-page.sync="itemsPerPage"
          :search="search"
          :hide-default-footer="allTagsAndLabels.length <= itemsPerPage"
        >
        <template v-slot:header v-if="allTagsAndLabels.length > itemsPerPage">
          <v-toolbar flat>
            <v-text-field
              v-model="search"
              clearable
              hide-details
              outlined
              dense
              prepend-inner-icon="mdi-magnify"
              label="Search for tags ..."
            ></v-text-field>
          </v-toolbar>
        </template>
        <template v-slot:default="props">
          <div
            v-for="item in props.items"
            :key="item.tag || item.label"
            @click="applyFilterChip(item.tag || item.label, item.tag ? 'tag' : '', item.tag ? 'term' : 'label')"
            style="cursor: pointer; font-size: 0.9em"
          >
            <v-row no-gutters class="pa-2 pl-5" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
              <v-icon v-if="item.label === '__ts_star'" left small color="amber">mdi-star</v-icon>
              <v-icon v-if="item.label === '__ts_comment'" left small>mdi-comment-multiple-outline</v-icon>
              <v-icon v-if="getQuickTag(item.tag)" small left :color="getQuickTag(item.tag).color">{{ getQuickTag(item.tag).label }}</v-icon>
              <span>
                {{ (item.tag || item.label) | formatLabelText }} (<small><strong>{{ item.count | compactNumber }}</strong></small>)
              </span>
            </v-row>
          </div>
        </template>
      </v-data-iterator>
    </div>
  </div>
</template>

<script>
import EventBus from '../../event-bus.js'

export default {
  props: [],
  data: function () {
    return {
      // TODO: Refactor this into a configurable option
      quickTags: [
        { tag: 'bad', color: 'red', textColor: 'white', label: 'mdi-alert-circle-outline' },
        { tag: 'suspicious', color: 'orange', textColor: 'white', label: 'mdi-help-circle-outline' },
        { tag: 'good', color: 'green', textColor: 'white', label: 'mdi-check-circle-outline' },
      ],
      itemsPerPage: 10,
      search: ''
    }
  },
  computed: {
    meta() {
      return this.$store.state.meta
    },
    tags() {
      return this.$store.state.tags
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
        .filter(item => item.tag || item.label) // Filter out items without tag or label
        .sort((a, b) => {
          const aLabel = a.tag || a.label
          const bLabel = b.tag || b.label

          const aIsLabel = !!a.label
          const bIsLabel = !!b.label

          // Sort labels before tags
          if (aIsLabel && !bIsLabel) return -1
          if (!aIsLabel && bIsLabel) return 1

          // Within labels and tags, sort by predefined order first, then alphabetically
          const aOrder = labelOrder.indexOf(aLabel)
          const bOrder = labelOrder.indexOf(bLabel)

          if (aOrder > -1 && bOrder > -1) return aOrder - bOrder // Sort by predefined order
          if (aOrder > -1) return -1 // Predefined labels come first
          if (bOrder > -1) return 1 // Predefined labels come first

          return aLabel.localeCompare(bLabel)
        })
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
