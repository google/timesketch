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
    <v-card flat class="pa-3 pt-0 mt-n3" color="transparent">
      <v-card class="d-flex align-start mb-1" outlined>
        <v-text-field
          v-model="filterString"
          @input="filterGraphByInput"
          class="pa-1"
          placeholder="Filter nodes and edges"
          label="Filter nodes and edges"
          append-icon="mdi-magnify"
          hide-details
          single-line
          dense
          filled
          flat
          solo
        >
        </v-text-field>
      </v-card>
      <v-toolbar dense flat color="transparent">
        <div>
          <span class="mr-2">
            <small>{{ nodes.length }} nodes and {{ edges.length }} edges</small>
          </span>
          <v-dialog v-if="edgeQuery" v-model="saveSelectionDialog" width="500">
            <template v-slot:activator="{ on, attrs }">
              <v-btn icon v-bind="attrs" v-on="on">
                <v-icon>mdi-content-save-outline</v-icon>
              </v-btn>
            </template>
            <v-card>
              <v-card-title> Save Selection </v-card-title>
            </v-card>
          </v-dialog>
        </div>
      </v-toolbar>
    </v-card>

    <div style="height: 85vh" ref="graphContainer">
      <cytoscape
        v-if="elements.length && showGraph"
        v-on:select="filterGraphBySelection($event)"
        v-on:unselect="unSelectAllElements($event)"
        :config="config"
        :preConfig="preConfig"
        :afterCreated="afterCreated"
      >
        <cy-element v-for="def in elements" :key="def.data.id" :definition="def"> </cy-element>
      </cytoscape>
    </div>

    <v-bottom-sheet
      hide-overlay
      persistent
      no-click-animation
      v-model="showTimelineView"
      @click:outside="closeTimelineView"
      scrollable
    >
      <v-card>
        <v-toolbar dense flat>
          <v-toolbar-title> Timeline </v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon>
            <v-icon v-if="!minimizeTimelineView" @click="minimizeTimelineView = true">mdi-window-minimize</v-icon>
            <v-icon v-if="minimizeTimelineView" @click="minimizeTimelineView = false">mdi-window-maximize</v-icon>
          </v-btn>
        </v-toolbar>
        <v-expand-transition>
          <v-card-text class="pa-4" style="height: 40vh" v-show="!minimizeTimelineView">
            <div v-if="!minimizeTimelineView">
              <!-- TODO: Replace with compact eventlist -->
              {{ edgeQuery }}
            </div>
          </v-card-text>
        </v-expand-transition>
      </v-card>
    </v-bottom-sheet>
  </v-container>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import EventBus from '../main'
import spread from 'cytoscape-spread'
import dagre from 'cytoscape-dagre'
import _ from 'lodash'

export default {
  props: ['graphId'],
  components: {},
  data: function () {
    return {
      showTimeline: false,
      saveSelectionDialog: false,
      showTimelineView: false,
      minimizeTimelineView: false,
      // imported
      showGraph: true,
      isLoading: false,
      filterString: '',
      graphs: {},
      savedGraphs: [], // check
      currentGraph: '',
      currentGraphCache: {},
      currentGraphCacheConfig: {},
      selectedGraphs: [], // check
      fadeOpacity: 7,
      elements: [],
      edgeQuery: '',
      maxEvents: 500,
      saveAsName: '',
      layouts: ['spread', 'dagre', 'circle', 'concentric', 'breadthfirst'],
      layoutName: 'spread',
      edgeStyles: ['bezier', 'taxi'],
      edgeStyle: 'bezier',
      config: {
        style: [
          {
            selector: 'node',
            style: {
              shape: 'roundrectangle',
              width: 'label',
              height: 'label',
              'compound-sizing-wrt-labels': 'include',
              'text-halign': 'center',
              'text-valign': 'center',
              color: '#FFFFFF',
              'font-size': '10',
              'font-weight': 'bold',
              'text-outline-width': '0px',
              padding: '7px',
              'background-color': 'gray',
              'text-outline-color': 'gray',
              'text-wrap': 'wrap',
              'text-max-width': '12em',
              label: 'data(label)',
            },
          },
          {
            selector: 'node:selected',
            style: {
              'overlay-color': 'black',
              'overlay-opacity': '0.3',
              'overlay-padding': '7px',
            },
          },
          {
            selector: "node[type = 'user']",
            style: {
              'background-color': '#FF756E',
              'text-outline-color': '#FF756E',
            },
          },
          {
            selector: "node[type = 'computer']",
            style: {
              'background-color': '#6992f3',
              'text-outline-color': '#ffffff',
            },
          },
          {
            selector: "node[type = 'file']",
            style: {
              'background-color': '#82b578',
              'text-outline-color': '#2b2b2b',
            },
          },
          {
            selector: "node[type = 'winservice']",
            style: {
              'background-color': '#9d8f35',
              'text-outline-color': '#2b2b2b',
            },
          },
          {
            selector: 'edge',
            style: {
              width: 1,
              'curve-style': 'bezier',
              'control-point-step-size': 70,
              'target-arrow-shape': 'triangle',
              'font-size': 11,
              'text-rotation': 'autorotate',
              'text-outline-width': 3,
              'text-outline-color': '#FFFFFF',
              label: 'data(label)',
            },
          },
          {
            selector: 'edge:selected',
            style: {
              width: 2,
              'line-color': '#333333',
              'source-arrow-color': '#333333',
              'target-arrow-color': '#333333',
            },
          },
          {
            selector: '.faded',
            style: {
              opacity: 0.07,
              color: '#333333',
            },
          },
        ],
        layout: {
          name: '',
          animate: false,
          prelayout: false,
          spacingFactor: 2,
        },

        // interaction options:
        minZoom: 0.1,
        maxZoom: 1.5,
        zoomingEnabled: true,
        userZoomingEnabled: true,
        panningEnabled: true,
        userPanningEnabled: true,
        boxSelectionEnabled: true,
        selectionType: 'single',
        touchTapThreshold: 8,
        desktopTapThreshold: 4,
        autolock: false,
        autoungrabify: false,
        autounselectify: false,

        // rendering options:
        headless: false,
        styleEnabled: true,
        hideEdgesOnViewport: false,
        hideLabelsOnViewport: false,
        textureOnViewport: false,
        motionBlur: false,
        motionBlurOpacity: 0.2,
        pixelRatio: 'auto',
      },
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    nodes() {
      return this.elements.filter((el) => el.group == 'nodes')
    },
    edges() {
      return this.elements.filter((el) => el.group == 'edges')
    },
  },
  methods: {
    toggleTimelineView: function () {
      this.showTimelineView = !this.showTimelineView
    },
    closeTimelineView: function () {
      if (this.$route.name != 'Graph') {
        this.showTimelineView = false
      }
    },
    setGraphPlugin: function (graphPlugin) {
      this.showTimelineView = false
      if (this.$route.name !== 'Graph') {
        this.$router.push({ name: 'Graph', params: { graphPlugin: graphPlugin } })
      }
      this.buildGraph(graphPlugin)
    },

    buildGraph: function (graphPlugin, refresh = false) {
      this.config.layout.name = this.layoutName

      let edgeStyle = this.config.style.filter((selector) => selector.selector === 'edge')
      edgeStyle[0].style['curve-style'] = this.edgeStyle

      if (typeof graphPlugin === 'object') {
        this.currentGraph = graphPlugin.name
      } else {
        this.currentGraph = graphPlugin
      }

      this.showGraph = false
      this.elements = []
      this.loadingTimeout = setTimeout(() => {
        if (!this.elements.length) {
          this.isLoading = true
        }
      }, 600)
      this.edgeQuery = ''
      let currentIndices = []
      let timelineIds = []
      if (this.$route.query.timeline) {
        timelineIds.push(parseInt(this.$route.query.timeline))
        refresh = true
      } else {
        this.sketch.timelines.forEach((timeline) => {
          currentIndices.push(timeline.searchindex.index_name)
        })
      }
      ApiClient.generateGraphFromPlugin(this.sketch.id, this.currentGraph, currentIndices, timelineIds, refresh)
        .then((response) => {
          let graphCache = response.data['objects'][0]
          let elementsCache = JSON.parse(graphCache.graph_elements)
          let configCache = JSON.parse(graphCache.graph_config)
          let elements = []
          let nodes
          let edges

          if ('elements' in elementsCache) {
            nodes = elementsCache['elements']['nodes']
            edges = elementsCache['elements']['edges']
          } else {
            nodes = elementsCache['nodes']
            edges = elementsCache['edges']
          }
          nodes.forEach((node) => {
            elements.push({ data: node.data, group: 'nodes' })
          })
          edges.forEach((edge) => {
            elements.push({ data: edge.data, group: 'edges' })
          })
          delete graphCache.graph_elements
          this.currentGraphCache = graphCache
          this.currentGraphCacheConfig = configCache
          this.elements = elements
          clearTimeout(this.loadingTimeout)
          this.showGraph = true
          this.isLoading = false
        })
        .catch((e) => {
          console.error(e)
        })
    },

    filterGraphByInput: function () {
      // Unselect all events to remove any potential left over
      this.cy.elements().unselect()

      // This is the collection of matched nodes/edges
      let selected = this.cy.elements().filter((ele) => ele.data('label').toLowerCase().includes(this.filterString))

      // Build the neighborhood
      this.showNeighborhood(selected)
    },

    filterGraphBySelection: function (event) {
      let selected = this.cy.filter(':selected')
      this.showNeighborhood(selected)
      this.showTimelineView = true
    },

    unSelectAllElements: function (event) {
      this.cy.elements().removeClass('faded')
      this.edgeQuery = null
      this.showTimelineView = false
    },

    buildNeighborhood: function (selected) {
      // Build a new collection to use as the neighborhood
      let neighborhood = this.cy.collection()

      // Build a neighborhood of nodes and edges.
      neighborhood = neighborhood.add(selected.filter('node').neighborhood())
      neighborhood = neighborhood.add(selected.filter('edge').connectedNodes())
      neighborhood = neighborhood.add(selected)

      return neighborhood
    },

    showNeighborhood: function (selected) {
      let neighborhood = this.buildNeighborhood(selected)

      if (selected.length === 0) {
        this.cy.elements().removeClass('faded')
        return
      }

      // Highlight the matched nodes/edges
      this.cy.elements().addClass('faded')
      neighborhood.removeClass('faded')

      // Build Opensearch query DSL to fetch edge events.
      let queryDsl = {
        query: {
          bool: {
            should: [],
          },
        },
        size: this.maxEvents,
      }
      neighborhood.forEach((element) => {
        if (element.group() === 'edges') {
          Object.keys(element.data().events).forEach((index) => {
            let boolMustQuery = {
              bool: {
                must: [{ ids: { values: element.data().events[index] } }, { term: { _index: { value: index } } }],
              },
            }
            queryDsl.query.bool.should.push(boolMustQuery)
          })
        }
      })
      this.edgeQuery = queryDsl
    },

    resizeCanvas: function () {
      let canvasHeight = this.$refs.graphContainer.clientHeight - 50
      let canvasWidth = this.$refs.graphContainer.clientWidth
      let canvas = document.getElementById('cytoscape-div')
      canvas.style.minHeight = canvasHeight + 'px'
      canvas.style.height = canvasHeight + 'px'
      canvas.style.minWidth = canvasWidth + 'px'
      canvas.style.width = canvasWidth + 'px'
    },
    // vue-cytoscape life-cycle hook, runs before graph is created.
    preConfig(cytoscape) {
      cytoscape.use(spread)
      cytoscape.use(dagre)
      this.resizeCanvas()
    },
    // vue-cytoscape life-cycle hook, runs after graph is created.
    async afterCreated(cy = null) {
      // Add Cytoscape "cy" objects to this component instance.
      if (cy !== null) {
        this.cy = cy
      } else {
        cy = this.cy
      }
      await cy
      this.setTheme()

      // Run the layout to render the graph elements.
      cy.layout(this.config.layout).run()
    },
    setTheme: function () {
      if (this.$vuetify.theme.dark) {
        this.cy
          .style()
          .selector('edge')
          .style({
            color: '#f5f5f5',
            'text-outline-color': '#25272c',
          })
          .update()
      } else {
        this.cy
          .style()
          .selector('edge')
          .style({
            color: '#333333',
            'text-outline-color': '#FFFFFF',
          })
          .update()
      }
    },
  },
  mounted() {
    window.addEventListener(
      'resize',
      _.debounce(() => {
        this.resizeCanvas()
      }, 250)
    )
    EventBus.$on('setGraphPlugin', this.setGraphPlugin)
  },
  watch: {
    '$vuetify.theme.dark'() {
      this.setTheme()
    },
  },
}
</script>

<style lang="scss" scoped>
</style>
