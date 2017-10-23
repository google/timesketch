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

export const style = ({nodeLabel, edgeLabel}): CytoscapeStyle => [
  {
    selector: 'node',
    style: {
      'shape': 'roundrectangle',
      'width': 'label',
      'height': 'label',
      'padding': 10,
      'label': (node) => nodeLabel(node.data()),
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
      'label': (edge) => edgeLabel(edge.data()),
      'font-size': 10,
      'text-rotation': 'autorotate',
    },
  },
]
