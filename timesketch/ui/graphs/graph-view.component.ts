import {Component, Input} from '@angular/core'

import {Graph} from '../api/graph.service'
import {CytoscapeSettings} from './cytoscape-settings.component'

export type Empty = {type: 'empty'}
export type Loading = {type: 'loading'}
export type Ready = {
  type: 'ready'
  graph: Graph
}

export type GraphViewState = Empty | Loading | Ready

function format(formatString: string, params: {[k: string]: string}): string {
  let result = formatString
  for (const [k, v] of Object.entries(params)) {
    result = result.replace('{' + k + '}', v)
  }
  return result
}

@Component({
  selector: 'ts-graphs-graph-view',
  templateUrl: './graph-view.component.html',
})
export class GraphViewComponent {
  // tslint:disable-next-line:no-unused-variable
  @Input() state: GraphViewState
  settings: CytoscapeSettings = {
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
    pixelRatio: ('auto' as any),
  }
  layout: Cy.LayoutOptions & {animationThreshold?: number} = {
    name: 'cose',
    animate: true,
    animationThreshold: 250,
    animationDuration: 1000,
    refresh: 20,
    fit: true,
    padding: 30,
    boundingBox: undefined,
    randomize: true,
    componentSpacing: 200,
    nodeRepulsion: () => 400000,
    nodeOverlap: 10,
    idealEdgeLength: () => 10,
    edgeElasticity: () => 100,
    nestingFactor: 5,
    gravity: 50,
    numIter: 1000,
    initialTemp: 200,
    coolingFactor: 0.95,
    minTemp: 1.0,
    weaver: false,
    nodeDimensionsIncludeLabels: false,
  }
  nodeLabel(node_data) {
    const {label_template} = (this.state as Ready).graph.schema.nodes[node_data.type]
    return format(label_template, node_data)
  }
  edgeLabel(edge_data) {
    const {label_template} = (this.state as Ready).graph.schema.edges[edge_data.type]
    return format(label_template, edge_data)
  }
  get style(): Array<Cy.Stylesheet & {padding?: number}> {
    return [
      {
        selector: 'node',
        style: {
          'shape': 'roundrectangle',
          'width': 'label',
          'height': 'label',
          'padding': 10,
          'label': (node) => this.nodeLabel(node.data()),
          'text-halign': 'center',
          'text-valign': 'center',
          'color': '#FFFFFF',
          'font-size': '10',
          'background-color': '#68BDF6',
          'border-color': '#5CA8DB',
          'border-width': '1',
          'text-wrap': 'wrap',
          'text-max-width': '20',
        },
      },
      {
        selector: "node[type = 'WindowsADUser']",
        style: {
          'background-color': '#FF756E',
          'border-color': '#E06760',
        },
      },
      {
        selector: "node[type = 'WindowsMachine']",
        style: {
          'background-color': '#68BDF6',
          'border-color': '#5CA8DB',
        },
      },
      {
        selector: "node[type = 'WindowsService']",
        style: {
          'background-color': '#6DCE9E',
          'border-color': '#60B58B',
        },
      },
      {
        selector: "node[type = 'WindowsServiceImagePath']",
        style: {
          'background-color': '#DE9BF9',
          'border-color': '#BF85D6',
        },
      },
      {
        selector: 'edge',
        style: {
          'width': 1,
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'label': (edge) => this.edgeLabel(edge.data()),
          'font-size': 10,
          'text-rotation': 'autorotate',
        },
      },
    ]
  }
}
