import {CytoscapeSettings, CytoscapeLayout, CytoscapeStyle} from './models'

export const settings: CytoscapeSettings = {
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

export const layout: CytoscapeLayout = {
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

export const style: CytoscapeStyle = [
  {
    selector: '*',
    style: {
      'font-family': 'FontAwesome, sans-serif',
    } as Cy.Css.Node,
  },
  {
    selector: 'node',
    style: {
      'shape': 'roundrectangle',
      'width': 'label',
      'height': 'label',
      'compound-sizing-wrt-labels': 'include',
      'label': (node) => node.scratch().label,
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
    },
  },
  {
    selector: 'node:selected',
    style: {
      'overlay-color': 'black',
      'overlay-opacity': '0.3',
      'overlay-padding': '7px',
    } as Cy.Css.Node,
  },
  {
    selector: "node[type = 'WindowsADUser']",
    style: {
      'background-color': '#FF756E',
      'text-outline-color': '#FF756E',
    },
  },
  {
    selector: "node[type = 'WindowsMachine']",
    style: {
      'background-color': '#68BDF6',
      'text-outline-color': '#68BDF6',
    },
  },
  {
    selector: "node[type = 'WindowsService']",
    style: {
      'background-color': '#6DCE9E',
      'text-outline-color': '#6DCE9E',
    },
  },
  {
    selector: "node[type = 'WindowsServiceImagePath']",
    style: {
      'background-color': '#DE9BF9',
      'text-outline-color': '#DE9BF9',
    },
  },
  {
    selector: 'edge',
    style: {
      'width': 1,
      'curve-style': 'bezier',
      'control-point-step-size': 70,
      'target-arrow-shape': 'triangle',
      'label': (edge) => edge.scratch().label,
      'font-size': 10,
      'text-rotation': 'autorotate',
      'text-outline-width': 4,
      'text-outline-color': '#FFFFFF',
    },
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
]
