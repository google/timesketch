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
    <section class="section" style="min-height: 100%;">
      <div class="container is-fluid">
        <div class="card">
          <header class="card-header" style="cursor: pointer">
            <span class="card-header-title">
              <span class="icon is-small"><i class="fas fa-network-wired"></i></span>
              <span style="margin-left:10px;">Graph</span>
            </span>
            <span class="card-header-icon">
              <span class="icon">
                <i class="fas fa-angle-down" aria-hidden="true"></i>
                <i class="fas fa-angle-up" aria-hidden="true"></i>
              </span>
            </span>
          </header>
          <button class="button" v-on:click="setConfig">Build graph</button>
          <button class="button" v-on:click="showGraph = false">Hide</button>

          <input class="input" v-model="filterString" v-on:keyup="filterGraphByInput"></input>

          <div class="card-content" >
            <cytoscape
              v-if="showGraph"
              v-on:select="filterGraphBySelection($event)"
              v-on:unselect="filterGraphBySelection($event)"
              v-on:tap="unSelectAllElements($event)"
              :config="config"
              :preConfig="preConfig"
              :afterCreated="afterCreated">
            </cytoscape>
          </div>
        </div>
      </div>
    </section>
</template>

<script>
import spread from "cytoscape-spread"
import ApiClient from "../../utils/RestApiClient"

let resolveCy = null
export const cyPromise = new Promise(resolve => (resolveCy = resolve))

export default {
  data() {
    return {
      showGraph: false,
      filterString: '',
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
          prelayout: {
            name: 'cose',
            animate: false,
            animationThreshold: 250,
            animationDuration: 1000,
            refresh: 20,
            fit: true,
            padding: 30,
            boundingBox: undefined,
            randomize: true,
            componentSpacing: 200,
            nodeRepulsion: 400000,
            nodeOverlap: 10,
            idealEdgeLength: 10,
            edgeElasticity: 100,
            nestingFactor: 5,
            gravity: 50,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0,
            weaver: false,
            nodeDimensionsIncludeLabels: false,
          }
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

        elements: null
      }
    }
  },
  computed: {
    sketch () {
        return this.$store.state.sketch
    },
    indices () {
        return this.$store.state.currentQueryFilter.indices
    }
  },
  methods: {
    setConfig: function () {
      ApiClient.getGraph(this.sketch.id)
        .then((response) => {
          this.config.elements = response.data
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

      // Build the neighborhood
      neighborhood = neighborhood.add(selected.filter('node').neighborhood())
      neighborhood = neighborhood.add(selected.filter('edge').connectedNodes())
      neighborhood = neighborhood.add(selected)

      // Highlight the matched nodes/edges
      this.cy.elements().addClass('faded')
      neighborhood.removeClass('faded')
    },
    filterGraphBySelection: function (event) {
      let selected = event.cy.filter(':selected')
      this.showNeighborhood(selected)
    },
    filterGraphByInput: function () {
      // Unselect all events to remove any potential left over
      this.cy.elements().unselect()

      // This is the collection of matched nodes/edges
      let selected = this.cy.elements().filter(ele => ele.data('label').toLowerCase().includes(this.filterString))

      // Build the neighborhood
      this.showNeighborhood(selected)
    },
    unSelectAllElements: function (event) {
      this.cy.elements().removeClass('faded')
    },
    preConfig (cytoscape) {
      cytoscape.use(spread)
    },
    afterCreated (cy) {
      this.cy = cy
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.element.style {
  height: 100%;
}
</style>
