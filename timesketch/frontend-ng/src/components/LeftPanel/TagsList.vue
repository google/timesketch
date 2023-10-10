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
    <div
      v-for="label in labels"
      :key="label.label"
      @click="applyFilterChip(term=label.label, termType='label')"
      style="cursor: pointer; font-size: 0.9em"
    >
      <v-row no-gutters class="pa-2 pl-5" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
        <v-icon v-if="label.label === '__ts_star'" left small color="amber">mdi-star</v-icon> <!--Add tooltip here? (star event)-->
        <v-icon v-if="label.label === '__ts_comment'" left small>mdi-comment-multiple-outline</v-icon>
        <span>
          {{ label.label | formatLabelText }} (<small
            ><strong>{{ label.count | compactNumber }}</strong></small
          >)
        </span>
      </v-row>
    </div>
    <div
      v-for="tag in assignedQuickTags"
      :key="tag.tag"
      @click="applyFilterChip(term=tag.tag, termField='tag', termType='term')"
      style="cursor: pointer; font-size: 0.9em"
    >
      <v-row no-gutters class="pa-2 pl-5" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
        <v-icon small left :color="getQuickTag(tag.tag).color">{{ getQuickTag(tag.tag).label }}</v-icon>
        <span
          >{{ tag.tag }} (<small
            ><strong>{{ tag.count | compactNumber }}</strong></small
          >)</span
        >
      </v-row>
    </div>
    <div
      v-for="tag in customTags"
      :key="tag.tag"
      @click="applyFilterChip(term=tag.tag, termField='tag', termType='term')"
      style="cursor: pointer; font-size: 0.9em"
    >
      <v-row no-gutters class="pa-2 pl-5" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
        <span
          >{{ tag.tag }} (<small
            ><strong>{{ tag.count | compactNumber }}</strong></small
          >)</span
        >
      </v-row>
    </div>
  </div>
</template>

<script>
import EventBus from '../../main'

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
