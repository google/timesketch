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
<template>
  <div>
    <v-row
      no-gutters
      style="cursor: pointer"
      class="pa-4"
      flat
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span
        ><v-icon left>mdi-source-branch</v-icon> Graphs (<small
          ><strong>{{ graphs.length + savedGraphs.length }} </strong></small
        >)</span
      >
    </v-row>

    <v-expand-transition>
      <div v-show="expanded">
        <!-- Saved graphs -->
        <v-row
          no-gutters
          v-for="graph in savedGraphs"
          :key="graph.id"
          class="pa-2 pl-5"
          :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
        >
          <router-link
            :to="{ name: 'Graph', query: { graph: graph.id } }"
            style="cursor: pointer; font-size: 0.9em; text-decoration: none"
          >
            <span :class="$vuetify.theme.dark ? 'dark-font' : 'light-font'" @click="setSavedGraph(graph.id)">{{
              graph.name
            }}</span>
          </router-link>
        </v-row>

        <!-- Graph plugins -->
        <v-row
          no-gutters
          v-for="graph in graphs"
          :key="graph.name"
          class="pa-2 pl-5"
          :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
        >
          <router-link
            :to="{ name: 'Graph', query: { plugin: graph.name } }"
            style="cursor: pointer; font-size: 0.9em; text-decoration: none"
          >
            <span :class="$vuetify.theme.dark ? 'dark-font' : 'light-font'" @click="setGraphPlugin(graph)">{{
              graph.display_name
            }}</span>
          </router-link>
        </v-row>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import EventBus from '../../main'

export default {
  props: [],
  data: function () {
    return {
      expanded: false,
      graphs: [],
      savedGraphs: [],
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
    setGraphPlugin(graph) {
      EventBus.$emit('setGraphPlugin', graph)
    },
    setSavedGraph(graphId) {
      EventBus.$emit('setSavedGraph', graphId)
    },
  },
  created() {
    ApiClient.getGraphPluginList()
      .then((response) => {
        this.graphs = response.data
      })
      .catch((e) => {
        console.error(e)
      })
    ApiClient.getSavedGraphList(this.sketch.id)
      .then((response) => {
        this.savedGraphs = response.data.objects[0]
      })
      .catch((e) => {
        console.error(e)
      })
  },
}
</script>
