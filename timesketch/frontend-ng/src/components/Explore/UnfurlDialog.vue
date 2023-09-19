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
  <v-card>
    <v-card-title>
      <v-icon large color="green">mdi-graph-outline</v-icon>
      <span class="text-h6 ml-2">Unfurl graph</span>
    </v-card-title>
    <v-card-subtitle class="pt-1">
      <span><b>Input:</b> {{ url }}</span>
    </v-card-subtitle>
    <v-card-text>
      <div v-show="!unfurlReady">
        <v-progress-linear
          color="primary"
          indeterminate>
        </v-progress-linear>
      </div>
      <div v-show="unfurlReady">
        <!-- Cytoscape container -->
        <div ref="graphContainer">
          <div ref="cy" width="100%" style="min-height: 400px; border: 1px; border-style: solid;"></div>
        </div>
      </div>
      <span>Powered by <a href="https://github.com/obsidianforensics/unfurl" target="_blank">dfir-unfurl</a></span>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        text
        @click="clearAndCancel"
      >
        close
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'

cytoscape.use(dagre)

export default {
  props: ['url'],
  data () {
    return {
      unfurlReady: false,
      unfurlData: {},
      config: {
        style: [
          {
            selector: 'node',
            style: {
              shape: 'roundrectangle',
              width: 'data(labelWidth)',
              height: 'data(labelHeight)',
              label: 'data(label)',
              'font-size': '10',
              'text-outline-width': '0px',
              padding: '7px',
              'background-color': '#e0e0e0',
              'text-outline-color': '#e0e0e0',
              'text-wrap': 'wrap',
              'text-max-width': '12em',
              'text-halign': 'center',
              'text-valign': 'center',
              color: '#000000',
            }
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
            }
          }
        ],

        layout: {
          name: 'dagre',
          animated: false,
          prelayout: false,
          spacingFactor: 1,
        }
      },
    }
  },
  methods: {
    clearAndCancel: function () {
      this.$emit('cancel')
    },
    getUnfurlData: function (url) {
      ApiClient.getUnfurlGraph(url).then((response) =>{
        this.unfurlData = response.data
        this.unfurlReady = true
        this.buildUnfurlGraph(this.unfurlData)
      }).catch((e) => {
        console.error('getting unfurl error: ', e)
      })
    },
    buildUnfurlGraph: function (data = {}, refresh = false) {
      this.cy.elements().remove()

      let elements = []
      data.nodes.forEach((node) => {
        elements.push({
          group: 'nodes',
          data: {
            id: node.id,
            label: node.label,
            labelWidth: node.label.length * 6,
            labelHeight: 13,
            context: node.title,
          },
        })
      })
      data.edges.forEach((edge) => {
        elements.push({
          group: 'edges',
          data: {
            id: `e${edge.from}${edge.to}`,
            source: edge.from,
            target: edge.to,
            label: edge.label,
            context: edge.title,
          },
        })
      })
      // console.log('elements', elements)

      this.cy.style(this.config.style)
      this.cy.add(elements)
      this.cy.layout(this.config.layout).run()
      // this.resizeGraphCanvas()
      // this.cy.resize()
      this.cy.fit()
      // console.log('cytoscape', this.cy)
    },
  },
  mounted () {
    this.unfurlReady = false
    this.getUnfurlData(this.url)
    this.cy = cytoscape({
      container: this.$refs.cy,
      ...this.config,
    })
    // TODO: Consider adding a mouseover event wrapper like https://github.com/cytoscape/cytoscape.js-popper
  },
}
</script>

<style scoped lang="scss"></style>
