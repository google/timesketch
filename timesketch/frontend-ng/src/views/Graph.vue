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
  <v-container fluid>
    <!-- Cytoscape container -->
    <div ref="graphContainer">
      <ts-cytoscape
        v-if="currentGraphPlugin || currentSavedGraph"
        :graph-plugin-name="currentGraphPlugin"
        :saved-graph-id="currentSavedGraph"
        canvas-height="80vh"
      ></ts-cytoscape>
    </div>
  </v-container>
</template>

<script>
import EventBus from '../main'
import TsCytoscape from '../components/Graph/Cytoscape'

export default {
  props: [],
  components: {
    TsCytoscape,
  },
  data: function () {
    return {
      currentGraphPlugin: null,
      currentSavedGraph: null,
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
    setSavedGraph: function (graphId) {
      if (this.$route.name !== 'Graph') {
        this.$router.push({ name: 'Graph', params: { graph: graphId } })
      }
      this.currentGraphPlugin = null
      this.currentSavedGraph = graphId
    },
    setGraphPlugin: function (graphPluginName) {
      if (this.$route.name !== 'Graph') {
        this.$router.push({ name: 'Graph', params: { graphPlugin: graphPluginName } })
      }
      this.currentSavedGraph = null
      this.currentGraphPlugin = graphPluginName
    },
  },
  mounted() {
    EventBus.$on('setGraphPlugin', this.setGraphPlugin)
    EventBus.$on('setSavedGraph', this.setSavedGraph)

    this.params = {
      graphId: this.$route.query.graph,
      pluginName: this.$route.query.plugin,
      timelineId: this.$route.query.timeline,
    }

    if (this.params.graphId) {
      this.setSavedGraph(Number(this.params.graphId))
    }

    if (this.params.pluginName) {
      this.setGraphPlugin(this.params.pluginName)
    }
  },

  beforeDestroy() {
    EventBus.$off('setGraphPlugin')
    EventBus.$off('setSavedGraph')
  },
}
</script>
