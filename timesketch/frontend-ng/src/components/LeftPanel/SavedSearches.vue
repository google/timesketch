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
    <div class="pa-4" flat :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
      <span style="cursor: pointer" @click="expanded = !expanded">
        <v-icon left>mdi-content-save-outline</v-icon>Saved Searches
      </span>
      <span class="float-right mr-2">
        <small
          ><strong>{{ meta.views.length }}</strong></small
        >
      </span>
    </div>

    <v-expand-transition>
      <div v-show="expanded">
        <v-row
          no-gutters
          v-for="savedSearch in meta.views"
          :key="savedSearch.name"
          class="pa-2 pl-5"
          :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
        >
          <div @click="setView(savedSearch)" style="cursor: pointer; font-size: 0.9em">{{ savedSearch.name }}</div>
        </v-row>
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
  },
  created() {},
}
</script>
