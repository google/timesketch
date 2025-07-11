<!--
Copyright 2025 Google Inc. All rights reserved.

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
      v-for="(savedSearch, key) in meta.views"
      :key="key"
      @mouseover="c_key = key"
      @mouseleave="c_key = -1"
      style="font-size: 0.9em"
    >
      <v-row no-gutters class="py-1 pl-5 pr-3" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
        <v-col @click="setView(savedSearch)" style="cursor: pointer"
          ><div class="mt-1">{{ savedSearch.name }}</div></v-col
        >
        <v-col cols="auto">
          <v-btn icon x-small style="cursor: pointer" @click="copySavedSearchUrlToClipboard(savedSearch.id)">
            <v-icon title="Copy link to this search" small v-show="key == c_key">mdi-link-variant</v-icon>
          </v-btn>
          <v-menu offset-y>
            <template v-slot:activator="{ on, attrs }">
              <v-btn small icon v-bind="attrs" v-on="on" class="mr-1">
                <v-icon title="More actions" small>mdi-dots-vertical</v-icon>
              </v-btn>
            </template>
            <v-list dense class="mx-auto">
              <v-list-item style="cursor: pointer" @click="copySavedSearchIdToClipboard(savedSearch.id)">
                <v-list-item-icon>
                  <v-icon small>mdi-identifier</v-icon>
                </v-list-item-icon>
                <v-list-item-title>Copy saved search ID</v-list-item-title>
              </v-list-item>
              <v-list-item style="cursor: pointer" @click="copySavedSearchUrlToClipboard(savedSearch.id)">
                <v-list-item-icon>
                  <v-icon small>mdi-link-variant</v-icon>
                </v-list-item-icon>
                <v-list-item-title>Copy link to this search</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </v-col>
      </v-row>
    </div>
  </div>
</template>

<script>
import EventBus from '../../event-bus.js'

export default {
  props: [],
  data: function () {
    return {
      c_key: -1,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  methods: {
    setView: function (savedSearch) {
      EventBus.$emit('setActiveView', savedSearch)
    },
    copySavedSearchIdToClipboard(savedSearchId) {
      try {
        navigator.clipboard.writeText(savedSearchId)
        this.infoSnackBar('Saved Search ID copied to clipboard')
      } catch (error) {
        this.errorSnackBar('Failed to load Saved Search ID into the clipboard!')
        console.error(error)
      }
    },
    copySavedSearchUrlToClipboard(savedSearchId) {
      try {
        let searchUrl = window.location.origin + this.$route.path + '?view=' + savedSearchId
        navigator.clipboard.writeText(searchUrl)
        this.infoSnackBar('Saved Search URL copied to clipboard')
      } catch (error) {
        this.errorSnackBar('Failed to load Saved Search URL into the clipboard!')
        console.error(error)
      }
    },
  },
}
</script>

<style scoped lang="scss"></style>
