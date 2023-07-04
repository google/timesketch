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
  <div>
    <div
      :style="meta.views && meta.views.length ? 'cursor: pointer' : ''"
      class="pa-4"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> <v-icon left>mdi-content-save-outline</v-icon> Saved Searches </span>
      <span class="float-right" style="margin-right: 10px">
        <small
          ><strong>{{ meta.views.length }}</strong></small
        >
      </span>
    </div>

    <v-expand-transition>
      <div v-show="expanded && meta.views.length">
        <div
          v-for="savedSearch in meta.views"
          :key="savedSearch.name"
          @click="setView(savedSearch)"
          style="cursor: pointer; font-size: 0.9em"
        >
          <v-row no-gutters class="py-1 pl-5 pr-3" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
            <v-col cols="11"
              ><div class="mt-1">{{ savedSearch.name }}</div></v-col
            >
            <v-col cols="1">
              <v-menu offset-y>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn small icon v-bind="attrs" v-on="on">
                    <v-icon small>mdi-dots-vertical</v-icon>
                  </v-btn>
                </template>

                <v-list dense class="mx-auto">
                  <v-list-item style="cursor: pointer" @click="copySavedSearchUrlToClipboard(savedSearch.id)">
                    <v-list-item-icon>
                      <v-icon small>mdi-link-variant</v-icon>
                    </v-list-item-icon>
                    <v-list-item-title>Copy link to this search </v-list-item-title>
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
import EventBus from '../../main'

export default {
  props: [],
  data: function () {
    return {
      expanded: false,
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
    copySavedSearchUrlToClipboard(savedSearchId) {
      try {
        let searchUrl = window.location.origin + this.$route.path + '?view=' + savedSearchId
        navigator.clipboard.writeText(searchUrl)
        this.infoSnackBar('Event URL copied to clipboard')
      } catch (error) {
        this.errorSnackBar('Failed to load Event URL into the clipboard')
        console.error(error)
      }
    },
  },
  created() {},
}
</script>
