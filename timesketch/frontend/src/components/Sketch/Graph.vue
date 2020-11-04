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
      <div class="container is-fluid">
        <div class="columns">
          <div class="column">
            <div class="card" v-if="!currentGraph" style="min-height: 620px;">
              <header class="card-header" style="border-bottom: 0;">
                <span class="card-header-title">Select a graph to get started</span>
              </header>
              <div class="card-content">
                <div class="field is-grouped">
                  <div class="field" v-for="(displayName, graphName) in graphs" :key="graph">
                    <button class="button is-rounded" v-on:click="buildGraph(graphName)">{{ displayName }}</button>
                  </div>
                </div>
              </div>
            </div>

            <div class="card" v-if="currentGraph" style="min-height: 620px;">
              <header class="card-header" style="border-bottom: 0;">
                <span class="card-header-title"><span v-if="currentGraph">{{ currentGraph }}</span></span>
                <input class="ts-search-input" v-if="currentGraph" v-model="filterString" v-on:keyup="filterGraphByInput" style="border-radius: 0; padding:25px;" placeholder="Filter nodes and edges"></input>

                <span class="card-header-icon">
                    <b-dropdown position="is-bottom-left" aria-role="menu" trap-focus append-to-body>
                      <button class="button is-outlined is-rounded is-small" slot="trigger" :disabled="!currentGraph">
                        <span class="icon is-small">
                          <i class="fas fa-cog"></i>
                        </span>
                        <span>Settings</span>
                      </button>
                      <b-dropdown-item aria-role="menu-item" :focusable="false" custom>
                        <div class="modal-card" style="width:500px; min-height: 300px;">
                          <br>
                          <p>Transparency for unselected elements</p>
                          <b-slider class="is-rounded" type="is-info" :custom-formatter="val => val + '%'" v-model="fadeOpacity" v-on:input="changeOpacity"></b-slider>
                        </div>
                      </b-dropdown-item>
                  </b-dropdown>
                </span>

              </header>
              <div class="card-content">
                <cytoscape
                  ref="cyRef"
                  v-if="showGraph"
                  v-on:select="filterGraphBySelection($event)"
                  v-on:unselect="unSelectAllElements($event)"
                  v-on:tap="unSelectAllElements($event)"
                  :config="config"
                  :preConfig="preConfig"
                  :afterCreated="afterCreated">
                  <cy-element
                    v-for="def in elements"
                    :key="def.data.id"
                    :definition="def">
                  </cy-element>
                </cytoscape>
              </div>
            </div>
          </div>

          <div class="column is-one-fifth" v-if="currentGraph">
            <div class="card" style="height: 100%;">
              <header class="card-header" style="border-bottom: 0;">
                <span class="card-header-title">Available graphs</span>
              </header>
              <div class="card-content">
                  <div v-for="(displayName, graphName) in graphs" :key="graph" style="margin-bottom: 7px;">
                    <button class="button is-rounded is-fullwidth" v-on:click="buildGraph(graphName)">{{ displayName }}</button>
                  </div>
              </div>
            </div>
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
import spread from "cytoscape-spread"
import ApiClient from "../../utils/RestApiClient"
import TsEventListCompact from "./EventListCompact"
import EventBus from "../../main"

export default {
  components: {
    TsEventListCompact
  },
  data() {
    return {
      showGraph: true,
      filterString: '',
      graphs: [],
      currentGraph: '',
      selectedGraphs: [],
      fadeOpacity: 7,
      elements: [],
      edgeQuery: '',
      maxEvents: 500,
      config: {
        style: [
          {
            selector: 'node',
            style: {
              'shape': 'roundrectangle',
              'width': 'label',
              'height': 'label',
              'compound-sizing-wrt-labels': 'include',
              'text-halign': 'center',
              'text-valign': 'center',
              'color': '#FFFFFF',
              'font-size': '10',
              'font-weight': 'bold',
              'text-outline-width': '0px',
              'padding': '7px',
              'background-color': 'gray',
              'text-outline-color': 'gray',
              'text-wrap': 'wrap',
              'text-max-width': '12em',
              'label': 'data(label)'
            }
          },
          {
            selector: 'node:selected',
            style: {
              'overlay-color': 'black',
              'overlay-opacity': '0.3',
              'overlay-padding': '7px',
            }
          },
          {
            selector: "node[type = 'username']",
            style: {
              'background-color': '#FF756E',
              'text-outline-color': '#FF756E',
            }
          },
          {
            selector: "node[type = 'computer']",
            style: {
              'background-color': '#6992f3',
              'text-outline-color': '#ffffff',
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 1,
              'curve-style': 'bezier',
              'control-point-step-size': 70,
              'target-arrow-shape': 'triangle',
              'font-size': 11,
              'text-rotation': 'autorotate',
              'text-outline-width': 3,
              'text-outline-color': '#FFFFFF',
              'label': 'data(label)'
            }
          },
          {
            selector: 'edge:selected',
            style: {
              'width': 2,
              'line-color': '#333333',
              'source-arrow-color': '#333333',
              'target-arrow-color': '#333333',
            }
          },
          {
            selector: '.faded',
            style: {
              'opacity': 0.07,
              'color': '#333333',
            }
          }
        ],
        layout: {
          name: "spread",
          animate: false,
          prelayout: false
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
        wheelSensitivity: 1,
        pixelRatio: 'auto',
      }
    }
  },
  computed: {
    sketch () {
        return this.$store.state.sketch
    }
  },
  methods: {
    buildGraph: function (graphName) {
      this.showGraph = false
      this.edgeQuery = ''
      ApiClient.getGraph(this.sketch.id, graphName).then((response) => {
          let elements = []
          response.data['nodes'].forEach((element) => {
            elements.push({data: element.data, group:'nodes'})
          })
          response.data['edges'].forEach((element) => {
            elements.push({data: element.data, group:'edges'})
          })
          this.elements = elements
          this.currentGraph = graphName
          this.showGraph = true
        }).catch((e) => {
          console.error(e)
        })
    },
    showNeighborhood: function (selected) {
      // Build a new collection to use as the neighborhood
      let neighborhood = this.cy.collection()

      if (selected.length === 0) {
        this.cy.elements().removeClass('faded')
        return
      }

      // Build a neighborhood of nodes and edges.
      neighborhood = neighborhood.add(selected.filter('node').neighborhood())
      neighborhood = neighborhood.add(selected.filter('edge').connectedNodes())
      neighborhood = neighborhood.add(selected)

      // Highlight the matched nodes/edges
      this.cy.elements().addClass('faded')
      neighborhood.removeClass('faded')

      // Build Elasticsearch query DSL to fetch edge events.
      let queryDsl = {
        'query': {
          'bool': {
            'should': []
          }
        },
        'size': this.maxEvents
      }
      neighborhood.forEach((element) => {
        if (element.group() === 'edges') {
          Object.keys(element.data().events).forEach((index) => {
            let boolMustQuery = {
              'bool': {
                'must': [
                    {'ids': {'values': element.data().events[index]}},
                    {'term': {'_index': {'value': index}}}
                  ]
              }
            }
            queryDsl.query.bool.should.push(boolMustQuery)
          })
        }
      })
      this.edgeQuery = queryDsl
    },

    filterGraphBySelection: function (event) {
      let selected = event.cy.filter(':selected')
      this.showNeighborhood(selected)
    },
    filterGraphByInput: function () {
      // Unselect all events to remove any potential left over
      this.cy.elements().unselect()

      // This is the collection of matched nodes/edges
      let selected = this.cy.elements()
        .filter(ele => ele.data('label')
          .toLowerCase()
          .includes(this.filterString))

      // Build the neighborhood
      this.showNeighborhood(selected)
    },
    unSelectAllElements: function (event) {
      this.cy.elements().removeClass('faded')
      this.edgeQuery = null
    },
    changeOpacity: function () {
      this.cy.style()
        .selector('.faded')
        .style({
          'opacity': this.fadeOpacity / 100
        }).update()
    },
    // vue-cytoscape life-cycle hook, runs before graph is created.
    preConfig (cytoscape) {
      cytoscape.use(spread)
    },
    // vue-cytoscape life-cycle hook, runs after graph is created.
    async afterCreated(cy=null) {
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
      this.isDarkTheme = localStorage.theme === 'dark'
      if (this.isDarkTheme) {
        this.cy.style()
          .selector('edge')
          .style({
            'color': '#f5f5f5',
            'text-outline-color': '#545454'
          }).update()
      } else {
        this.cy.style()
          .selector('edge')
          .style({
            'color': '#333333',
            'text-outline-color': '#FFFFFF'
          }).update()
      }
    }
  },
  created() {
    ApiClient.getGraphList().then((response) => {
        this.graphs = response.data
      }).catch((e) => {
        console.error(e)
    })
    EventBus.$on('isDarkTheme', this.setTheme)
  }
}
</script>
<style lang="scss"></style>
