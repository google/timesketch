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
        ><v-icon left>mdi-family-tree</v-icon> Graphs (<small><strong>n/a</strong></small
        >)</span
      >
    </v-row>

    <v-expand-transition>
      <div v-show="expanded">
        <ul>
          <li v-for="graph in graphs" :key="graph.name" @click="setGraphPlugin(graph)">
            {{ graph.name }}
          </li>
        </ul>
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
  },
  created() {
    ApiClient.getGraphPluginList()
      .then((response) => {
        this.graphs = response.data
      })
      .catch((e) => {
        console.error(e)
      })
  },
}
</script>
