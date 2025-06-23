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
  <div
    v-if="iconOnly"
    class="pa-4"
    style="cursor: pointer"
    @click="
      $emit('toggleDrawer')
      expanded = true
    "
  >
    <v-icon left>mdi-content-save-outline</v-icon>
    <div style="height: 1px"></div>
  </div>
  <div v-else>
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
        <ts-saved-searches-list></ts-saved-searches-list>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import TsSavedSearchesList from './SavedSearchesList.vue'

export default {
  props: {
    iconOnly: Boolean,
  },
  components: {
    TsSavedSearchesList,
  },
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
  methods: {},
}
</script>
