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
      <v-row
        no-gutters
        class="py-1 pl-5 pr-3"
        :class="theme.global.current.value.dark ? 'dark-hover' : 'light-hover'"
      >
        <v-col @click="setView(savedSearch)" style="cursor: pointer"
          ><div class="mt-1">{{ savedSearch.name }}</div></v-col
        >
        <v-col cols="auto">
          <v-icon
            variant="text"
            icon="mdi-link-variant"
            size="x-small"
            class="mr-2"
            style="cursor: pointer"
            @click="copySavedSearchUrlToClipboard(savedSearch.id)"
            title="Copy link to this search"
            v-show="key == c_key"
          ></v-icon>
          <v-menu offset-y>
            <template v-slot:activator="{ props }">
              <v-icon
                variant="text"
                size="small"
                icon="mdi-dots-vertical"
                v-bind="props"
                class="mr-1"
                title="More actions"
              ></v-icon>
            </template>
            <v-list dense class="mx-auto">
              <v-list-item style="cursor: pointer" @click="copySavedSearchIdToClipboard(savedSearch.id)" prepend-icon="mdi-identifier">
                <v-list-item-title>Copy saved search ID</v-list-item-title>
              </v-list-item>
              <v-list-item
                style="cursor: pointer"
                @click="copySavedSearchUrlToClipboard(savedSearch.id)"
                prepend-icon="mdi-link-variant"
              >
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
import { useAppStore } from '@/stores/app'
import { useTheme } from 'vuetify'

export default {
  name: 'SavedSearchesList',
  setup() {
    const theme = useTheme()
    return { theme }
  },
  data: function () {
    return {
      appStore: useAppStore(),
      c_key: -1,
    }
  },
  computed: {
    sketch() {
      return this.appStore.sketch
    },
    meta() {
      return this.appStore.meta
    },
  },
  methods: {
    setView: function (savedSearch) {
      EventBus.$emit('setActiveView', savedSearch)
      this.$emit('search-triggered')
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
