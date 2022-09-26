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
      <v-icon v-bind="attrs" v-on="on">mdi-tag-plus-outline</v-icon>
    </template>

    <v-card min-width="500px" class="mx-auto">
      <v-card-text>
        <strong>Quick tags</strong>
        <v-chip-group>
          <v-chip
            v-for="tag in quickTags"
            :key="tag.tag"
            :color="tag.color"
            :text-color="tag.textColor"
            class="text-center"
            small
            @click="addTags(tag.tag)"
          >
            <v-icon small left> {{ tag.label }} </v-icon>
            {{ tag.tag }}</v-chip
          >
        </v-chip-group>
        <br />
        <v-combobox
          v-model="selectedTags"
          :items="tags"
          label="Add tags.."
          outlined
          chips
          small-chips
          multiple
        ></v-combobox>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="addTags(selectedTags)">Save</v-btn>
      </v-card-actions>
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
      selectedTags: [],
      // TODO: Refactor this into a configurable option
      quickTags: [
        { tag: 'bad', color: 'red', textColor: 'white', label: 'mdi-alert-circle-outline' },
        { tag: 'suspicious', color: 'orange', textColor: 'white', label: 'mdi-help-circle-outline' },
        { tag: 'good', color: 'green', textColor: 'white', label: 'mdi-check-circle-outline' },
      ],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    tags() {
      return this.$store.state.tags.map((tag) => tag.tag)
    },
  },
  methods: {
    addTags: function (tagsToAdd) {
      if (!Array.isArray(tagsToAdd)) {
        tagsToAdd = [tagsToAdd]
      }

      tagsToAdd.forEach((tag) => {
        if (this.event._source.tag.indexOf(tag) === -1) {
          this.event._source.tag.push(tag)
          ApiClient.tagEvents(this.sketch.id, [this.event], [tag])
            .then((response) => {})
            .catch((e) => {
              console.error('Cannot tag event')
            })
        }
        this.selectedTags = []
        this.showMenu = false
      })
    },
  },
}
</script>

<style scoped lang="scss"></style>
