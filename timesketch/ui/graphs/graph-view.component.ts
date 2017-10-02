import {Component, Input} from '@angular/core'

import {CytoscapeSettings} from './cytoscape-settings.component'

export type Empty = {type: 'empty'}
export type Loading = {type: 'loading'}
export type Ready = {
  type: 'ready'
  elements: Cy.ElementsDefinition | Cy.ElementDefinition[]
}

export type GraphViewState = Empty | Loading | Ready

@Component({
  selector: 'ts-graphs-graph-view',
  templateUrl: './graph-view.component.html',
})
export class GraphViewComponent {
  // tslint:disable-next-line:no-unused-variable
  @Input() state: GraphViewState
  settings: CytoscapeSettings = {
    // interaction options:
    minZoom: 1e-50,
    maxZoom: 1e50,
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
  style: Array<Cy.Stylesheet & {padding?: number}> = [
    {
      selector: 'node',
      style: {
        'shape': 'roundrectangle',
        'width': 'label',
        'height': 'label',
        'padding': 10,
        'label': 'data(label)',
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
      selector: "node[type = 'User']",
      style: {
        'background-color': '#FF756E',
        'border-color': '#E06760',
      },
    },
    {
      selector: "node[type = 'Machine']",
      style: {
        'background-color': '#68BDF6',
        'border-color': '#5CA8DB',
      },
    },
    {
      selector: "node[type = 'Service']",
      style: {
        'background-color': '#6DCE9E',
        'border-color': '#60B58B',
      },
    },
    {
      selector: "node[type = 'ServiceImagePath']",
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
        'label': 'data(label)',
        'font-size': 10,
        'text-rotation': 'autorotate',
      },
    },
  ]
}
