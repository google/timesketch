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
  <div
    v-if="iconOnly"
    class="pa-4"
    style="cursor: pointer"
    @click="$emit('toggleDrawer'); expanded = true"
  >
    <v-icon start>mdi-content-save-outline</v-icon>
    <div style="height: 1px"></div>
  </div>
  <div v-else>
    <div
      :style="meta.views && meta.views.length ? 'cursor: pointer' : ''"
      class="pa-4"
      @click="expanded = !expanded"
      :class="this.$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> <v-icon start>mdi-content-save-outline</v-icon> Saved Searches </span>
      <span class="float-right" style="margin-right: 10px">
        <small
          ><strong>{{ meta.views.length }}</strong></small
        >
      </span>
    </div>

    <v-expand-transition>
      <div v-show="expanded && meta.views.length">
        <div
          v-for="(savedSearch, key) in meta.views"
          :key="key"
          @mouseover="c_key = key"
          @mouseleave="c_key = -1"
          style="font-size: 0.9em"
        >
          <v-row no-gutters class="py-1 pl-5 pr-3" :class="this.$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
            <v-col @click="setView(savedSearch)" style="cursor: pointer"
              ><div class="mt-1">{{ savedSearch.name }}</div></v-col
            >
            <v-col cols="auto">
              <v-btn icon size="x-small" style="cursor: pointer" @click="copySavedSearchUrlToClipboard(savedSearch.id)">
                <v-icon title="Copy link to this search" size="small" v-show="key == c_key">mdi-link-variant</v-icon>
              </v-btn>
              <v-menu offset-y>
                <template v-slot:activator="{ props }">
                  <v-btn v-bind="props"  size="small" icon class="mr-1">
                    <v-icon title="More actions" size="small">mdi-dots-vertical</v-icon>
                  </v-btn>
                </template>
                <v-list density="compact" class="mx-auto">
                  <v-list-item style="cursor: pointer" @click="copySavedSearchIdToClipboard(savedSearch.id)">
                    <v-list-item-icon>
                      <v-icon size="small">mdi-identifier</v-icon>
                    </v-list-item-icon>
                    <v-list-item-title>Copy saved search ID</v-list-item-title>
                  </v-list-item>
                  <v-list-item style="cursor: pointer" @click="copySavedSearchUrlToClipboard(savedSearch.id)">
                    <v-list-item-icon>
                      <v-icon size="small">mdi-link-variant</v-icon>
                    </v-list-item-icon>
                    <v-list-item-title>Copy link to this search</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </v-col>
          </v-row>
        </div>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import EventBus from '../../event-bus.js'

export default {
  props: {
    iconOnly: Boolean,
  },
  data: function () {
    return {
      expanded: false,
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
        const searchUrl = window.location.origin + this.$route.path + '?view=' + savedSearchId
        navigator.clipboard.writeText(searchUrl)
        this.infoSnackBar('Saved Search URL copied to clipboard')
      } catch (error) {
        this.errorSnackBar('Failed to load Saved Search URL into the clipboard!')
        console.error(error)
      }
    },
  },
  created() {},
}
</script>
