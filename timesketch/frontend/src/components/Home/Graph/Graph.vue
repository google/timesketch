<!--
Copyright 2020 Google Inc. All rights reserved.

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
    <section class="section">
      <div class="container is-fluid" style="height: 75vh;" ref="graphContainer">
        <div class="card" style="height: 100%;">
          <header class="card-header" style="border-bottom: 0;">
            <div v-if="currentGraph">
              <ts-dropdown>
                <template v-slot:dropdown-trigger-element>
                  <a class="button ts-search-dropdown" style="background-color: transparent;">
                    <span class="icon is-small" style="margin-right: 10px; margin-top:2px; font-size: 0.6em;">
                      <i class="fas fa-project-diagram"></i>
                    </span>
                    <div v-if="currentGraph" style="margin-right: 7px;">
                      <strong>{{ currentGraph }}</strong>
                    </div>
                    <b-icon icon="chevron-down" style="font-size: 0.6em;"></b-icon>
                  </a>
                </template>

                <div
                  class="ts-dropdown-item"
                  v-for="graphPlugin in graphs"
                  :key="graphPlugin.name"
                  v-on:click="buildGraph(graphPlugin)"
                >
                  <router-link :to="{ name: 'GraphExplore', query: { plugin: graphPlugin.name } }">{{
                    graphPlugin.display_name
                  }}</router-link>
                </div>
                <div
                  class="ts-dropdown-item"
                  v-for="savedGraph in savedGraphs"
                  :key="savedGraph.id"
                  v-on:click="buildSavedGraph(savedGraph)"
                >
                  <router-link :to="{ name: 'GraphExplore', query: { graph: savedGraph.id } }">{{
                    savedGraph.name
                  }}</router-link>
                </div>
              </ts-dropdown>
            </div>

            <ts-dropdown>
              <template v-slot:dropdown-trigger-element>
                <a class="button ts-search-dropdown" style="background-color: transparent;">
                  <span v-if="currentGraphCacheConfig.filter.timelineIds.length">
                    {{ getTimelineFromId(currentGraphCacheConfig.filter.timelineIds[0])[0].name }}
                  </span>
                  <strong v-else>Choose timeline</strong>
                  <b-icon icon="chevron-down" style="font-size: 0.6em;"></b-icon>
                </a>
              </template>

              <div
                class="ts-dropdown-item"
                v-for="timeline in sketch.timelines"
                :key="timeline.id"
                v-on:click="buildGraph(currentGraph)"
              >
                <router-link :to="{ name: 'GraphExplore', query: { plugin: currentGraph, timeline: timeline.id } }">{{
                  timeline.name
                }}</router-link>
              </div>
            </ts-dropdown>

            <input
              class="ts-search-input"
              v-if="currentGraph"
              v-model="filterString"
              v-on:keyup="filterGraphByInput"
              style="border-radius: 0; padding:25px;"
              placeholder="Filter nodes and edges"
            />

            <span class="card-header-icon" v-if="currentGraph">
              <ts-dropdown position="is-bottom-left" width="500px">
                <template v-slot:dropdown-trigger-element>
                  <button class="button is-outlined is-rounded is-small" slot="trigger" :disabled="!currentGraph">
                    <span class="icon is-small">
                      <i class="fas fa-cog"></i>
                    </span>
                    <span>Settings</span>
                  </button>
                </template>
                <div>
                  <div class="ts-dropdown-item">
                    <b-field label="Transparency for unselected elements">
                      <b-slider
                        class="is-rounded"
                        type="is-info"
                        :custom-formatter="val => val + '%'"
                        v-model="fadeOpacity"
                        v-on:input="changeOpacity"
                      ></b-slider>
                    </b-field>

                    <b-field label="Layout type">
                      <b-radio
                        v-for="layout in layouts"
                        :key="layout"
                        v-model="layoutName"
                        :native-value="layout"
                        type="is-info"
                        v-on:input="buildGraph({ name: currentGraph })"
                        :disabled="!hasGraphCache"
                      >
                        <span>{{ layout }}</span>
                      </b-radio>
                    </b-field>

                    <b-field label="Edge style">
                      <b-radio
                        v-for="edge in edgeStyles"
                        :key="edge"
                        v-model="edgeStyle"
                        :native-value="edge"
                        type="is-info"
                        v-on:input="buildGraph({ name: currentGraph })"
                        :disabled="!hasGraphCache"
                      >
                        <span>{{ edge }}</span>
                      </b-radio>
                    </b-field>
                  </div>
                </div>
              </ts-dropdown>

              <ts-dropdown position="is-bottom-left" width="500px">
                <template v-slot:dropdown-trigger-element :disabled="!edgeQuery">
                  <button class="button is-outlined is-rounded is-small">
                    <span class="icon is-small">
                      <i class="fas fa-save"></i>
                    </span>
                    <span>Save selection</span>
                  </button>
                </template>

                <strong>Save selected graph</strong>
                <br /><br />
                <div class="field">
                  <div class="control">
                    <input v-model="saveAsName" class="input" type="text" placeholder="Graph name" required />
                  </div>
                </div>
                <button class="button is-small" v-on:click="saveSelection">Save</button>
              </ts-dropdown>

              <button
                class="button is-outlined is-rounded is-small"
                style="margin-left:7px;"
                v-on:click="buildGraph({ name: currentGraph }, true)"
                :disabled="!hasGraphCache"
              >
                <span class="icon is-small">
                  <i class="fas fa-sync-alt"></i>
                </span>
                <span>Refresh cache</span>
              </button>

              <button class="button is-outlined is-rounded is-small" style="margin-left:7px;" v-on:click="cy.fit()">
                <span class="icon is-small">
                  <i class="fas fa-eye"></i>
                </span>
                <span>Fit to canvas</span>
              </button>
            </span>
          </header>
          <div class="card-content">
            <b-loading :is-full-page="false" v-model="isLoading" :can-cancel="false">
              <div class="lds-ripple">
                <div></div>
                <div></div>
              </div>
              <div style="position: absolute; margin-top:120px;">
                Generating graph: <b>{{ currentGraph }}</b>
              </div>
            </b-loading>
            <div class="no-data" v-if="!elements.length && showGraph && currentGraph">Empty graph</div>
            <cytoscape
              ref="cyRef"
              v-if="elements.length && showGraph"
              v-on:select="filterGraphBySelection($event)"
              v-on:unselect="unSelectAllElements($event)"
              v-on:tap="unSelectAllElements($event)"
              :config="config"
              :preConfig="preConfig"
              :afterCreated="afterCreated"
            >
              <cy-element v-for="def in elements" :key="def.data.id" :definition="def"> </cy-element>
            </cytoscape>
            <span v-if="hasGraphCache">
              <span
                ><i
                  >Generated
                  {{
                    $moment
                      .utc(currentGraphCache.updated_at)
                      .local()
                      .fromNow()
                  }}</i
                >
              </span>
              <a
                class="is-small"
                style="text-decoration: underline; margin-left:15px;"
                v-on:click="buildGraph({ name: currentGraph }, true)"
              >
                <span>Refresh</span>
              </a>
            </span>
            <span
              style="color:red; margin-left:20px;"
              v-for="timelineId in currentGraphCacheConfig.filter.timelineIds"
              :key="timelineId"
            >
              Note: Graph generated for timeline: {{ getTimelineFromId(timelineId)[0].name }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <section class="section" v-if="edgeQuery">
      <div class="container is-fluid">
        <div class="card">
          <header class="card-header">
            <span class="card-header-title">Events for selected edges</span>
          </header>
          <div class="card-content">
            <ts-event-list-compact v-if="edgeQuery" :query-dsl="edgeQuery"></ts-event-list-compact>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import spread from 'cytoscape-spread'
import dagre from 'cytoscape-dagre'
import ApiClient from '../../utils/RestApiClient'
import TsEventListCompact from '../Explore/EventListCompact'
import TsDropdown from '../Common/Dropdown'
import EventBus from '../../main'
import _ from 'lodash'

export default {
  components: { TsEventListCompact, TsDropdown },
  data() {
    return {
      showGraph: true,
      isLoading: false,
      filterString: '',
      graphs: {},
      savedGraphs: [],
      currentGraph: '',
      currentGraphCache: {},
      currentGraphCacheConfig: {},
      selectedGraphs: [],
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
    hasGraphCache() {
      return Object.keys(this.currentGraphCache).length !== 0
    },
  },
  methods: {
    buildGraph: function(graphPlugin, refresh = false) {
      this.config.layout.name = this.layoutName

      let edgeStyle = this.config.style.filter(selector => selector.selector === 'edge')
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
        this.sketch.timelines.forEach(timeline => {
          currentIndices.push(timeline.searchindex.index_name)
        })
      }
      ApiClient.generateGraphFromPlugin(this.sketch.id, this.currentGraph, currentIndices, timelineIds, refresh)
        .then(response => {
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
          nodes.forEach(node => {
            elements.push({ data: node.data, group: 'nodes' })
          })
          edges.forEach(edge => {
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
        .catch(e => {
          console.error(e)
        })
    },
    buildSavedGraph: function(savedGraph) {
      this.config.layout.name = 'preset'
      this.currentGraph = savedGraph.name
      this.currentGraphCache = {}
      this.showGraph = false
      this.elements = []
      this.loadingTimeout = setTimeout(() => {
        if (!this.elements.length) {
          this.isLoading = true
        }
      }, 600)
      this.edgeQuery = ''

      let graphId = ''
      if (typeof savedGraph === 'object') {
        graphId = savedGraph.id
      } else {
        graphId = savedGraph
      }

      ApiClient.getSavedGraph(this.sketch.id, graphId)
        .then(response => {
          this.currentGraph = response.data['objects'][0].name
          let elements = JSON.parse(response.data['objects'][0].graph_elements)
          let nodes = elements.filter(ele => ele.group === 'nodes')
          let edges = elements.filter(ele => ele.group === 'edges')
          let orderedElements = []
          nodes.forEach(node => {
            node.selected = false
            orderedElements.push(node)
          })
          edges.forEach(edge => {
            edge.selected = false
            orderedElements.push(edge)
          })
          clearTimeout(this.loadingTimeout)
          this.elements = orderedElements
          this.showGraph = true
          this.isLoading = false
        })
        .catch(e => {
          console.error(e)
        })
    },
    buildNeighborhood: function(selected) {
      // Build a new collection to use as the neighborhood
      let neighborhood = this.cy.collection()

      // Build a neighborhood of nodes and edges.
      neighborhood = neighborhood.add(selected.filter('node').neighborhood())
      neighborhood = neighborhood.add(selected.filter('edge').connectedNodes())
      neighborhood = neighborhood.add(selected)

      return neighborhood
    },
    showNeighborhood: function(selected) {
      let neighborhood = this.buildNeighborhood(selected)

      if (selected.length === 0) {
        this.cy.elements().removeClass('faded')
        return
      }

      // Highlight the matched nodes/edges
      this.cy.elements().addClass('faded')
      neighborhood.removeClass('faded')

      // Build Elasticsearch query DSL to fetch edge events.
      let queryDsl = {
        query: {
          bool: {
            should: [],
          },
        },
        size: this.maxEvents,
      }
      neighborhood.forEach(element => {
        if (element.group() === 'edges') {
          Object.keys(element.data().events).forEach(index => {
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
    saveSelection: function() {
      let selected = this.cy.filter(':selected')
      let neighborhood = this.buildNeighborhood(selected)
      let elements = neighborhood.jsons()
      this.showGraph = false
      this.elements = elements
      this.currentGraph = this.saveAsName
      this.showGraph = true
      ApiClient.saveGraph(this.sketch.id, this.saveAsName, elements).then(response => {
        let savedGraph = response.data['objects'][0]
        this.savedGraphs.push(savedGraph)
      })
      this.saveAsName = ''
    },
    filterGraphBySelection: function(event) {
      let selected = this.cy.filter(':selected')
      this.showNeighborhood(selected)
    },
    filterGraphByInput: function() {
      // Unselect all events to remove any potential left over
      this.cy.elements().unselect()

      // This is the collection of matched nodes/edges
      let selected = this.cy.elements().filter(ele =>
        ele
          .data('label')
          .toLowerCase()
          .includes(this.filterString)
      )

      // Build the neighborhood
      this.showNeighborhood(selected)
    },
    unSelectAllElements: function(event) {
      this.cy.elements().removeClass('faded')
      this.edgeQuery = null
    },
    changeOpacity: function() {
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
    resizeCanvas: function() {
      let canvasHeight = this.$refs.graphContainer.clientHeight - 100
      let canvasWidth = this.$refs.graphContainer.clientWidth - 100
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
    setTheme: function() {
      this.isDarkTheme = localStorage.theme === 'dark'
      if (this.isDarkTheme) {
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
    getTimelineFromId(id) {
      return this.sketch.timelines.filter(timeline => timeline.id === id)
    },
  },
  created() {
    window.addEventListener(
      'resize',
      _.debounce(() => {
        this.resizeCanvas()
      }, 250)
    )
    ApiClient.getGraphPluginList()
      .then(response => {
        this.graphs = response.data
      })
      .catch(e => {
        console.error(e)
      })
    ApiClient.getSavedGraphList(this.sketch.id)
      .then(response => {
        let graphs = response.data['objects'][0]
        if (graphs !== undefined) {
          this.savedGraphs = response.data['objects'][0]
        }
      })
      .catch(e => {
        console.error(e)
      })
    EventBus.$on('isDarkTheme', this.setTheme)

    this.params = {
      graphId: this.$route.query.graph,
      pluginName: this.$route.query.plugin,
      timelineId: this.$route.query.timeline,
    }

    if (this.params.graphId) {
      this.buildSavedGraph(this.params.graphId)
    }

    if (this.params.pluginName) {
      this.buildGraph(this.params.pluginName)
    }
  },
}
</script>
<style lang="scss">
.lds-ripple {
  display: inline-block;
  position: relative;
  width: 80px;
  height: 80px;
}
.lds-ripple div {
  position: absolute;
  border: 4px solid var(--spinner-color);
  opacity: 1;
  border-radius: 50%;
  animation: lds-ripple 1s cubic-bezier(0, 0.2, 0.8, 1) infinite;
}
.lds-ripple div:nth-child(2) {
  animation-delay: -0.5s;
}
@keyframes lds-ripple {
  0% {
    top: 36px;
    left: 36px;
    width: 0;
    height: 0;
    opacity: 1;
  }
  100% {
    top: 0px;
    left: 0px;
    width: 72px;
    height: 72px;
    opacity: 0;
  }
}

.no-data {
  align-items: center;
  justify-content: center;
  overflow: hidden;
  display: flex;
}
</style>
