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
  <!-- <v-menu v-model="showMenu" offset-x :close-on-content-click="false"> -->
  <v-menu v-model="showMenu" :offset-x="true" :close-on-content-click="false">
    <template v-slot:activator="{ props }">
      <v-icon
        title="Modify tags"
        v-if="assignedTags.length > 0"
        v-bind="props"
        class="ml-1"
        >mdi-tag-plus</v-icon
      >
      <v-icon title="Modify tags" v-else v-bind="props" class="ml-1"
        >mdi-tag-plus-outline</v-icon
      >
    </template>

    <v-card
      min-width="500px"
      class="mx-auto"
      max-width="500px"
      min-height="260px"
    >
      <v-btn class="float-right mr-1 mt-1" icon @click="showMenu = false">
        <v-icon title="Close dialog">mdi-close</v-icon>
      </v-btn>
      <v-card-text>
        <strong>Quick tags</strong>
        <div class="mt-2 mb-6" style="display: flex; flex-wrap: wrap; align-items: center;">
          <v-chip
            v-for="tag in quickTags"
            :key="tag.tag"
            class="mr-1"
            :color="tag.color"
            :prepend-icon="tag.label"
            :text="tag.tag"
            size="small"
            variant="flat"
            :disabled="assignedTags.includes(tag.tag) ? true : false"
            @click="addTags(tag.tag)"
            @click.stop="showMenu = false"
            title="Add quick tag"
          >
          </v-chip>
        </div>

        <strong>Assigned tags</strong>
        <div class="mt-2" style="display: flex; flex-wrap: wrap; align-items: center;">
          <v-chip
            v-for="tag in assignedTags"
            :key="tag"
            class="mr-1"
            :color="getQuickTag(tag) ? getQuickTag(tag).color : ''"
            :prepend-icon="getQuickTag(tag) ? getQuickTag(tag).label : ''"
            :text="tag"
            variant="flat"
            size="small"
            closable
            @click:close="removeTags(tag)"
            title="Remove "
          >
          </v-chip>
        </div>
        <br />
        <v-combobox
          v-model="selectedTags"
          v-model:search="search"
          :hide-no-data="!search"
          :items="customTags"
          label="Add new tag"
          chips
          hide-selected
          multiple
          variant="outlined"
          @update:modelValue="addTags(selectedTags[0])"
        >
          <template v-slot:no-data>
            <v-list-item>
              <span class="subheading">Create new tag: </span>
              <v-chip class="ml-1" small>
                {{ search }}
              </v-chip>
            </v-list-item>
          </template>
          <template v-slot:item="{ item }">
            <v-chip size="small">
              {{ item }}
            </v-chip>
          </template>
        </v-combobox>
      </v-card-text>
    </v-card>
  </v-menu>
</template>

<script>
import ApiClient from "../../utils/RestApiClient";
import { useAppStore } from "@/stores/app";

export default {
  props: ["event"],
  data() {
    return {
      appStore: useAppStore(),
      showMenu: false,
      listItems: [],
      selectedTags: null,
      // TODO: Refactor this into a configurable option
      quickTags: [
        {
          tag: "bad",
          color: "red",
          label: "mdi-alert-circle-outline",
        },
        {
          tag: "suspicious",
          color: "warning",
          label: "mdi-help-circle-outline",
        },
        {
          tag: "good",
          color: "success",
          label: "mdi-check-circle-outline",
        },
      ],
      search: null,
    };
  },
  computed: {
    sketch() {
      return this.appStore.sketch;
    },
    tags() {
      return this.appStore.tags.map((tag) => tag.tag);
    },
    assignedTags() {
      if (!this.event._source.tag) return [];
      return this.event._source.tag;
    },
    customTags() {
      if (!this.event._source.tag) return [];
      // returns all custom tags available for a sketch without the ones that are already applied to an event
      let customTags = this.tags.filter((tag) => !this.getQuickTag(tag));
      customTags = customTags.filter((tag) => !this.assignedTags.includes(tag));
      customTags.sort((a, b) => {
        return a.localeCompare(b);
      });
      return customTags;
    },
  },
  methods: {
    getQuickTag(tag) {
      return this.quickTags.find((el) => el.tag === tag);
    },
    removeTags(tag) {
      ApiClient.untagEvents(this.sketch.id, [this.event], [tag])
        .then((response) => {
          this.event._source.tag.splice(this.event._source.tag.indexOf(tag), 1);
          this.appStore.updateTimelineTags({
            sketchId: this.sketch.id,
            tag: tag,
            num: -1,
          });
        })
        .catch((e) => {
          console.error(e);
        });
    },
    addTags: function (tagToAdd) {
      if (!this.event._source.hasOwnProperty("tag")) {
        this.event._source.tag = []
      }

      for (const tag of tagToAdd) {
        if (this.event._source.tag.indexOf(tag) !== -1) {
          tagToAdd.splice(tagToAdd.indexOf(tag), 1);
        }
      }

      ApiClient.tagEvents(this.sketch.id, [this.event], [tagToAdd])
        .then((response) => {
        this.event._source.tag.push(tagToAdd);
        this.appStore.updateTimelineTags( {
            sketchId: this.sketch.id,
            tag: tagToAdd,
            num: 1,
          });
        })
        .catch((e) => {
          console.error("Cannot tag event! Error:" + e);
        });
      this.$nextTick(() => {
        this.selectedTags = null;
        this.search = null;
      });
    },
  },
};
</script>

<style scoped lang="scss"></style>
