export type Graph = {
  elements: Cy.ElementsDefinition
  schema: {
    nodes: {[type: string]: {
      label_template: string
    }}
    edges: {[type: string]: {
      label_template: string
    }}
  }
}

type Empty = {type: 'empty'}
type Loading = {type: 'loading'}
type Ready = {
  type: 'ready'
  graph: Graph
}

export type GraphState = Empty | Loading | Ready

export type CytoscapeLayout = Cy.LayoutOptions & {animationThreshold?: number}

export type CytoscapeStyle = Array<Cy.Stylesheet & {padding?: number}>

/**
 * A subset of Cytoscape initialization options.
 * Does not include the first 6: container, elements, style, layout, zoom, pan.
 * @see {@link http://js.cytoscape.org/#core/initialisation}
 */
export type CytoscapeSettings = {
  // interaction options
  minZoom?: number
  maxZoom?: number
  zoomingEnabled?: boolean
  userZoomingEnabled?: boolean
  panningEnabled?: boolean
  userPanningEnabled?: boolean
  boxSelectionEnabled?: boolean
  selectionType?: 'additive' | 'single'
  touchTapThreshold?: number
  desktopTapThreshold?: number
  autolock?: boolean
  autoungrabify?: boolean
  autounselectify?: boolean

  // rendering options
  headless?: boolean
  styleEnabled?: boolean
  hideEdgesOnViewport?: boolean
  hideLabelsOnViewport?: boolean
  textureOnViewport?: boolean
  motionBlur?: boolean
  motionBlurOpacity?: number
  wheelSensitivity?: number
  pixelRatio?: number
}

export type PredefinedQuery = {
  name: string
  query: string
}
