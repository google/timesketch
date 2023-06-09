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
          <!-- Save graph dialog -->
          <v-dialog v-model="saveGraphDialog" width="500">
            <template v-slot:activator="{ on, attrs }">
              <v-btn icon :disabled="!edgeQuery" v-bind="attrs" v-on="on" title="Save selected graph">
                <v-icon>mdi-content-save-outline</v-icon>
              </v-btn>
            </template>
            <v-card class="pa-4">
              <h3>Save selected elements</h3>
              <br />
              <v-text-field
                v-model="saveAsName"
                required
                placeholder="Name your graph"
                outlined
                dense
                autofocus
                @focus="$event.target.select()"
              ></v-text-field>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn text @click="saveGraphDialog = false"> Cancel </v-btn>
                <v-btn color="primary" depressed @click="saveGraph" :disabled="!saveAsName"> Save </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>

          <v-btn icon v-on:click="resizeCanvas()" :disabled="!currentGraph" title="Fit to canvas">
            <v-icon>mdi-fit-to-page-outline</v-icon>
          </v-btn>
          <!-- Graph settings menu -->
          <v-menu
            v-model="graphSettingsMenu"
            offset-y
            :close-on-content-click="false"
            :close-on-click="true"
            content-class="menu-with-gap"
          >
            <template v-slot:activator="{ on, attrs }">
              <v-btn icon v-bind="attrs" v-on="on" :disabled="!currentGraph || !graphPluginName" title="Graph settings">
                <v-icon> mdi-cog-outline </v-icon>
              </v-btn>
            </template>

            <v-card class="pa-4 pt-5" width="600">
              <h5>Layout type</h5>
              <v-radio-group row v-model="layoutName">
                <v-radio
                  v-for="layout in layouts"
                  :key="layout"
                  :label="layout"
                  :value="layout"
                  @click="buildGraph(currentGraph)"
                ></v-radio>
              </v-radio-group>

              <h5>Edge style</h5>
              <v-radio-group row v-model="edgeStyle">
                <v-radio
                  v-for="edge in edgeStyles"
                  :key="edge"
                  :label="edge"
                  :value="edge"
                  @click="buildGraph(currentGraph)"
                ></v-radio>
              </v-radio-group>

              <h5>Transparency for unselected elements</h5>
              <v-slider v-model="fadeOpacity" @change="changeOpacity" :max="100" :min="0" thumb-label>
                <template v-slot:thumb-label="{ value }"> {{ value }}% </template>
              </v-slider>
            </v-card>
          </v-menu>
        </div>
        <v-spacer></v-spacer>
        <div v-if="Object.keys(currentGraphCache).length">
          <i
            ><small>Generated {{ currentGraphCache.updated_at | timeSince }}</small></i
          >
          <v-btn
            icon
            class="ml-1"
            title="Refresh graph"
            v-on:click="buildGraph({ name: currentGraph }, true)"
            :disabled="!currentGraph"
          >
            <v-icon>mdi-refresh</v-icon>
          </v-btn>
        </div>
      </v-toolbar>
    </v-card>

    <div v-if="isLoading" class="pa-4">
      <v-progress-linear indeterminate color="primary"></v-progress-linear>
    </div>

    <v-card flat class="pa-4" v-if="!elements.length && !isLoading"> No data to generate graph </v-card>

    <!-- Cytoscape container -->
    <div ref="graphContainer" :style="{ height: canvasHeight }">
      <div ref="cy" width="100%" :style="{ 'min-height': canvasHeight }"></div>
    </div>

    <!-- Event list for selected edges -->
    <v-bottom-sheet hide-overlay persistent no-click-animation v-model="showTimelineView" scrollable>
      <v-card>
        <v-toolbar dense flat>
          <strong>Timeline for {{ selectedEdgesCount }} selected edge(s)</strong>
          <v-spacer></v-spacer>
          <v-btn icon :disabled="timelineViewHeight > 40" @click="increaseTimelineViewHeight()">
            <v-icon>mdi-chevron-up</v-icon>
          </v-btn>
          <v-btn icon :disabled="timelineViewHeight === 0" @click="decreaseTimelineViewHeight()">
            <v-icon>mdi-chevron-down</v-icon>
          </v-btn>
          <v-btn icon @click="showTimelineView = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        <v-divider></v-divider>
        <v-expand-transition>
          <v-card-text :style="{ height: timelineViewHeight + 'vh' }" v-show="!minimizeTimelineView">
            <ts-event-list
              :query-request="queryRequest"
              :items-per-page="maxEvents"
              disable-save-search
            ></ts-event-list>
          </v-card-text>
        </v-expand-transition>
      </v-card>
    </v-bottom-sheet>
  </v-container>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import EventBus from '../../main'
import cytoscape from 'cytoscape'
import spread from 'cytoscape-spread'
import dagre from 'cytoscape-dagre'

import TsEventList from '../Explore/EventList'

cytoscape.use(spread)
cytoscape.use(dagre)

export default {
  props: {
    graphPluginName: {
      type: String,
      default: null,
    },
    savedGraphId: {
      type: Number,
      default: null,
    },
    canvasHeight: {
      type: String,
      default: '85vh',
    },
    disableZoom: {
      type: Boolean,
      default: false,
    },
  },
  components: {
    TsEventList,
  },
  data: function () {
    return {
      saveGraphDialog: false,
      graphSettingsMenu: false,
      showTimelineView: false,
      timelineViewHeight: 40,
      minimizeTimelineView: false,
      isLoading: false,
      filterString: '',
      graphs: {},
      currentGraph: '',
      currentGraphCache: {},
      currentGraphCacheConfig: {},
      fadeOpacity: 7,
      elements: [],
      selectedEdgesCount: 0,
      edgeQuery: '',
      maxEvents: 40,
      queryFilter: {
        from: 0,
        terminate_after: 40,
        size: this.maxEvents,
        indices: ['_all'],
        order: 'asc',
        chips: [],
      },
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
          name: 'spread',
          animate: false,
          prelayout: false,
          spacingFactor: 2,
        },

        // interaction options:
        minZoom: 0.1,
        maxZoom: 1.5,
        zoomingEnabled: true,
        userZoomingEnabled: !this.disableZoom,
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
      return this.elements.filter((el) => el.group === 'nodes')
    },
    edges() {
      return this.elements.filter((el) => el.group === 'edges')
    },
    queryRequest() {
      if (!this.edgeQuery) {
        return
      }
      return { queryDsl: this.edgeQuery, queryFilter: this.queryFilter, incognito: true }
    },
  },
  methods: {
    increaseTimelineViewHeight: function () {
      this.minimizeTimelineView = false
      if (this.timelineViewHeight > 70) {
        return
      }
      this.timelineViewHeight += 30
    },
    decreaseTimelineViewHeight: function () {
      this.minimizeTimelineView = false
      if (this.timelineViewHeight < 50) {
        this.minimizeTimelineView = true
        this.timelineViewHeight = 0
        return
      }
      this.timelineViewHeight -= 30
    },
    buildSavedGraph: function (savedGraph) {
      // Remove existing elements to clean up the canvas.
      this.cy.elements().remove()

      this.isLoading = true
      this.config.layout.name = 'preset'
      this.currentGraph = savedGraph.name
      this.currentGraphCache = {}
      this.elements = []
      this.edgeQuery = ''
      let graphId = ''
      if (typeof savedGraph === 'object') {
        graphId = savedGraph.id
      } else {
        graphId = savedGraph
      }
      ApiClient.getSavedGraph(this.sketch.id, graphId)
        .then((response) => {
          this.currentGraph = response.data['objects'][0].name
          let elements = JSON.parse(response.data['objects'][0].graph_elements)
          let nodes = elements.filter((ele) => ele.group === 'nodes')
          let edges = elements.filter((ele) => ele.group === 'edges')
          let orderedElements = []
          nodes.forEach((node) => {
            node.selected = false
            orderedElements.push(node)
          })
          edges.forEach((edge) => {
            edge.selected = false
            orderedElements.push(edge)
          })
          clearTimeout(this.loadingTimeout)
          this.elements = orderedElements
          this.isLoading = false
          this.updateCytoscape(elements)
          this.resizeCanvas()
        })
        .catch((e) => {
          console.error(e)
        })
    },
    buildGraph: function (graphPlugin, refresh = false) {
      // Remove existing elements to clean up the canvas.
      this.cy.elements().remove()

      this.isLoading = true
      this.showTimelineView = false
      this.config.layout.name = this.layoutName

      let edgeStyle = this.config.style.filter((selector) => selector.selector === 'edge')
      edgeStyle[0].style['curve-style'] = this.edgeStyle

      if (typeof graphPlugin === 'object') {
        this.currentGraph = graphPlugin.name
      } else {
        this.currentGraph = graphPlugin
      }

      this.elements = []
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
          this.isLoading = false
          this.updateCytoscape(elements)
          this.resizeCanvas()
        })
        .catch((e) => {
          console.error(e)
        })
    },
    updateCytoscape: function (elements) {
      this.cy.style(this.config.style)
      this.cy.elements().remove()
      this.cy.add(elements)
      this.cy.layout(this.config.layout).run()
      this.setTheme()
    },
    saveGraph: function () {
      let selected = this.cy.filter(':selected')
      let neighborhood = this.buildNeighborhood(selected)
      let elements = neighborhood.jsons()
      this.elements = elements
      this.currentGraph = this.saveAsName
      ApiClient.saveGraph(this.sketch.id, this.saveAsName, elements)
        .then((response) => {
          this.$store.dispatch('updateSavedGraphs', this.sketch.id)
          this.$router.push({ name: 'Graph', query: { graph: response.data.objects[0].id } })
        })
        .catch((e) => {
          this.errorSnackBar('Unable to save graph')
          console.error(e)
        })
      this.saveAsName = ''
      this.saveGraphDialog = false
    },
    filterGraphByInput: function () {
      // Unselect all events to remove any potential left over
      this.cy.elements().unselect()

      // This is the collection of matched nodes/edges
      let selected = this.cy
        .elements()
        .filter((ele) => ele.data('label').toLowerCase().includes(this.filterString.toLowerCase()))

      // Build the neighborhood (without fetching edge events)
      this.showNeighborhood(selected, false)
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
      this.selectedEdgesCount = 0
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
    showNeighborhood: function (selected, fetchEvents = true) {
      let neighborhood = this.buildNeighborhood(selected)

      if (selected.length === 0) {
        this.cy.elements().removeClass('faded')
        return
      }

      // Highlight the matched nodes/edges
      this.cy.elements().addClass('faded')
      neighborhood.removeClass('faded')

      // Build Opensearch query DSL to fetch edge events.
      // Exit early if edge events are not requested.
      if (!fetchEvents) {
        return
      }

      let queryDsl = {
        query: {
          bool: {
            should: [],
          },
        },
      }
      neighborhood.forEach((element) => {
        if (element.group() === 'edges') {
          Object.keys(element.data().events).forEach((index) => {
            this.selectedEdgesCount++
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
      // Exit early if there is no graph canvas
      if (!this.$refs.graphContainer) {
        return
      }

      let canvasHeight = this.$refs.graphContainer.clientHeight
      let canvasWidth = this.$refs.graphContainer.clientWidth
      let canvas = this.$refs.cy
      canvas.style.minHeight = canvasHeight + 'px'
      canvas.style.height = canvasHeight + 'px'
      canvas.style.minWidth = canvasWidth + 'px'
      canvas.style.width = canvasWidth + 'px'
      this.cy.resize()
      this.cy.fit()
    },
    resizeCanvasWithDelay: function () {
      this.resizeTimeout = setTimeout(() => {
        this.resizeCanvas()
      }, 250)
    },
    changeOpacity: function () {
      if (!this.cy) {
        return
      }
      this.cy
        .style()
        .selector('.faded')
        .style({
          opacity: this.fadeOpacity / 100,
        })
        .update()
    },
    setTheme: function () {
      if (!this.cy) {
        return
      }
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
    window.addEventListener('resize', this.resizeCanvasWithDelay)
    EventBus.$on('toggleLeftPanel', this.resizeCanvasWithDelay)

    // Setup Cytoscape instance
    this.cy = cytoscape({
      container: this.$refs.cy,
      ...this.config,
    })

    this.cy.on('select', (event) => {
      this.filterGraphBySelection(event)
    })
    this.cy.on('unselect', (event) => {
      this.unSelectAllElements(event)
    })

    if (this.graphPluginName) {
      this.buildGraph(this.graphPluginName)
    }

    if (this.savedGraphId) {
      this.buildSavedGraph(this.savedGraphId)
    }
  },
  beforeDestroy() {
    EventBus.$off('toggleLeftPanel')
  },
  watch: {
    '$vuetify.theme.dark'() {
      this.setTheme()
    },
    graphPluginName() {
      if (!this.graphPluginName) {
        return
      }
      this.buildGraph(this.graphPluginName)
    },
    savedGraphId() {
      if (!this.savedGraphId) {
        return
      }
      this.buildSavedGraph(this.savedGraphId)
    },
    $route(to, from) {
      // Detect route change, and close the timeline view if the user us navigating
      // to a different page.
      if (from === to) {
        return
      }
      this.showTimelineView = false
    },
  },
}
</script>
