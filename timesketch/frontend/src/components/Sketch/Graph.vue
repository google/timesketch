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

    <b-sidebar :fullheight="true" :right="true" v-model="sidebarOpen" :can-cancel="true">
      <section class="section">
          <div style="padding: 30px">
            <div class="card">
              <div class="card-content">
                <header class="card-header">
                  <span class="card-header-title">Graph view settings</span>
                </header>
                <p>Transparency for unselected elements</p>
                <b-slider class="is-rounded" type="is-info" :custom-formatter="val => val + '%'" v-model="fadeOpacity" v-on:input="changeOpacity"></b-slider>
              </div>
            </div>
          </div>
      </section>
    </b-sidebar>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <header class="card-header">
            <span class="card-header-title">Available graphs</span>
          </header>
          <div class="card-content">
            <div class="field is-grouped">
              <p class="control" v-for="graph in graphs" :key="graph">
                <button class="button is-rounded" v-on:click="buildGraph(graph)">{{ graph }}</button>
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
    <section class="section">
      <div class="container is-fluid">

        <div class="card">
          <header class="card-header">
            <span class="card-header-title" v-if="currentGraph">{{ currentGraph }}</span>
            <span class="card-header-icon" v-if="currentGraph">
              <button class="button is-small" @click="sidebarOpen = true"><i class="fas fa-cog"></i>Settings</button>
            </span>
          </header>
          <div class="card-content">
            <div class="field" v-if="currentGraph">
              <div class="control" style="width: 100%;">
                <input class="ts-search-input" v-model="filterString" v-on:keyup="filterGraphByInput" placeholder="Filter nodes and edges"></input>
              </div>
            </div>
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
    </section>
    <section class="section" v-if="edgeQueryString">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <ts-event-list-compact :queryString="edgeQueryString"></ts-event-list-compact>
          </div>
        </div>
      </div>
    </section>
    <br>
  </div>
</template>

<script>
import spread from "cytoscape-spread"
import ApiClient from "../../utils/RestApiClient"
import TsEventListCompact from "./EventListCompact"

export default {
  components: {
    TsEventListCompact
  },
  data() {
    return {
      showGraph: true,
      sidebarOpen: false,
      filterString: '',
      graphs: [],
      currentGraph: '',
      selectedGraphs: [],
      fadeOpacity: 7,
      showOpacitySlider: false,
      elements: [],
      edgeQueryString: '',
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
              'font-size': 10,
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
      this.showOpacitySlider = true

      // Build ES query to show edge events.
      // TODO: Consider using chips filters instead of query string.
      let e = []
      this.edgeQueryString = []
      neighborhood.forEach((element, idx) => {
        let esIndex = element.data().es_index
        let esDocId = element.data().es_doc_id
        if (element.group() === 'edges') {
          if (idx > 1 && e.length) {
            e.push(' OR ')
          }
          e.push('(_index:' + esIndex + ' AND _id:"' + esDocId + '")')
        }
      })
      this.edgeQueryString = e.join(" ")

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
      this.showOpacitySlider = false
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
      document.getElementById("cytoscape-div")
        .style.minHeight=window.innerHeight -700 + "px";
    },
    // vue-cytoscape life-cycle hook, runs after graph is created, but before
    // events has been added.
    async afterCreated(cy=null) {
      // Add Cytoscape "cy" objects to this component instance.
      if (cy !== null) {
          this.cy = cy
      } else {
          cy = this.cy
      }
      await cy
      // Run the layout to render the graph elements.
      cy.layout(this.config.layout).run()
    }
  },
  created() {
    ApiClient.getGraphList()
      .then((response) => {
        this.graphs = response.data
      }).catch((e) => {
      console.error(e)
    })
  }
}
</script>
<style lang="scss">

.b-sidebar .sidebar-content {
  width:40%;
  background-color: #f5f5f5;
}

</style>
