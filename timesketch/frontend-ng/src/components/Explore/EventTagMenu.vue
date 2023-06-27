<!--
Copyright 2022 Google Inc. All rights reserved.

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
  <v-menu v-model="showMenu" offset-x :close-on-content-click="false">
    <template v-slot:activator="{ on, attrs }">
      <v-icon v-if="assignedTags.length > 0" v-bind="attrs" v-on="on" class="ml-1">mdi-tag-plus</v-icon>
      <v-icon v-else v-bind="attrs" v-on="on" class="ml-1">mdi-tag-plus-outline</v-icon>
    </template>

    <v-card min-width="500px" class="mx-auto" max-width="500px" min-height="260px">
      <v-btn class="float-right mr-1 mt-1" icon @click="showMenu = false">
        <v-icon>mdi-close</v-icon>
      </v-btn>
      <v-card-text>
        <strong>Quick tags</strong>
        <v-chip-group>
          <v-chip
            v-for="tag in quickTags"
            :key="tag.tag"
            :color="tag.color"
            :text-color="tag.textColor"
            :disabled="assignedTags.includes(tag.tag) ? true : false"
            class="text-center"
            small
            @click="addTags(tag.tag)"
            @click.stop="showMenu = false"
          >
            <v-icon small left> {{ tag.label }} </v-icon>
            {{ tag.tag }}
          </v-chip>
        </v-chip-group>
        <strong>Assigned tags</strong>
        <v-chip-group column>
          <v-chip
            v-for="tag in assignedTags"
            :key="tag"
            :color="getQuickTag(tag) ? getQuickTag(tag).color : ''"
            :text-color="getQuickTag(tag) ? getQuickTag(tag).textColor : ''"
            class="text-center"
            small
            close
            @click:close="removeTags(tag)"
          >
            <v-icon v-if="getQuickTag(tag)" small left>{{ getQuickTag(tag).label }}</v-icon>
            {{ tag }}
          </v-chip>
        </v-chip-group>
        <br />
        <v-combobox
          v-model="selectedTags"
          :hide-no-data="!search"
          :items="customTags"
          :search-input.sync="search"
          hide-selected
          label="Add tags ..."
          small-chips
          outlined
          @change="addTags(selectedTags)"
        >
          <template v-slot:no-data>
            <v-list-item>
              <span class="subheading">Create new tag: </span>
              <v-chip
                class="ml-1"
                small
              >
                {{ search }}
              </v-chip>
            </v-list-item>
          </template>
          <template v-slot:item="{ item }">
            <v-chip
              small
            >
              {{ item }}
            </v-chip>
          </template>
        </v-combobox>
      </v-card-text>
    </v-card>
  </v-menu>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  props: ['event'],
  data() {
    return {
      showMenu: false,
      listItems: [],
      selectedTags: null,
      // TODO: Refactor this into a configurable option
      quickTags: [
        { tag: 'bad', color: 'red', textColor: 'white', label: 'mdi-alert-circle-outline' },
        { tag: 'suspicious', color: 'orange', textColor: 'white', label: 'mdi-help-circle-outline' },
        { tag: 'good', color: 'green', textColor: 'white', label: 'mdi-check-circle-outline' },
      ],
      search: null,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    tags() {
      return this.$store.state.tags.map((tag) => tag.tag)
    },
    assignedTags() {
      if (!this.event._source.tag) return []
      return this.event._source.tag
    },
    customTags() {
      if (!this.event._source.tag) return []
      // returns all custom tags available for a sketch without the ones that are already applied to an event
      let customTags = this.tags.filter((tag) => !this.getQuickTag(tag))
      customTags = customTags.filter((tag) => !this.assignedTags.includes(tag))
      customTags.sort((a, b) => { return a.localeCompare(b)})
      return customTags
    },
  },
  methods: {
    getQuickTag(tag) {
      return this.quickTags.find((el) => el.tag === tag)
    },
    removeTags(tag) {
      ApiClient.untagEvents(this.sketch.id, [this.event], [tag])
        .then((response) => {
          this.event._source.tag.splice(this.event._source.tag.indexOf(tag), 1)
          this.$store.dispatch('updateTimelineTags', { sketchId: this.sketch.id, tag: tag, num: -1 })
        })
        .catch((e) => {
          console.error(e)
        })
    },
    addTags: function (tagToAdd) {
      if (!this.event._source.hasOwnProperty('tag')) {
        this.$set(this.event._source, 'tag', [])
      }

      for (const tag of tagToAdd) {
        if (this.event._source.tag.indexOf(tag) !== -1) {
          tagToAdd.splice(tagToAdd.indexOf(tag), 1)
        }
      }

      ApiClient.tagEvents(this.sketch.id, [this.event], [tagToAdd])
        .then((response) => {
          this.$set(this.event._source.tag, this.event._source.tag.length, tagToAdd)
          this.$store.dispatch('updateTimelineTags', { sketchId: this.sketch.id, tag: tagToAdd, num: 1 })
        })
        .catch((e) => {
          console.error('Cannot tag event! Error:' + e)
        })
      this.$nextTick(() => {
        this.selectedTags = null
        this.search = null
      })
    },
  },
}
</script>

<style scoped lang="scss"></style>
