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
<!--
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
    <v-icon left>mdi-source-branch</v-icon>
    <div style="height: 1px"></div>
  </div>
  <div v-else>
    <div
      style="cursor: pointer"
      class="pa-4"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> <v-icon left>mdi-source-branch</v-icon> Graphs </span>

      <span class="float-right" style="margin-right: 10px">
        <small
          ><strong>{{ graphs.length + savedGraphs.length }}</strong></small
        >
      </span>
    </div>

    <v-expand-transition>
      <div v-show="expanded">
        <!-- Saved graphs -->
        <div v-show="savedGraphs.length">
          <v-subheader>Saved Graphs</v-subheader>
          <router-link
            v-for="graph in savedGraphs"
            :key="graph.id"
            :to="{ name: 'Graph', query: { graph: graph.id } }"
            style="cursor: pointer; font-size: 0.9em; text-decoration: none"
          >
            <v-row
              no-gutters
              @click="setSavedGraph(graph.id)"
              class="pa-2 pl-5"
              :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
            >
              <span :class="$vuetify.theme.dark ? 'dark-font' : 'light-font'">{{ graph.name }}</span>
            </v-row>
          </router-link>
        </div>

        <!-- Graph plugins -->
        <div v-show="graphs.length">
          <v-subheader>Plugins</v-subheader>
          <router-link
            v-for="graph in graphs"
            :key="graph.name"
            :to="{ name: 'Graph', query: { plugin: graph.name } }"
            style="cursor: pointer; font-size: 0.9em; text-decoration: none"
          >
            <v-row
              no-gutters
              @click="setGraphPlugin(graph.name)"
              class="pa-2 pl-5"
              :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
            >
              <span :class="$vuetify.theme.dark ? 'dark-font' : 'light-font'">{{ graph.display_name }}</span>
            </v-row>
          </router-link>
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
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    graphs() {
      return this.$store.state.graphPlugins
    },
    savedGraphs() {
      return this.$store.state.savedGraphs
    },
  },
  methods: {
    setGraphPlugin(graph) {
      EventBus.$emit('setGraphPlugin', graph)
    },
    setSavedGraph(graphId) {
      EventBus.$emit('setSavedGraph', graphId)
    },
  },
}
</script>
-->
