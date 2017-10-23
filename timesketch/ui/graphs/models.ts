/** Generic helpers for 'RemoteData' pattern. */
type Empty = {type: 'empty'}
type Loading = {type: 'loading'}

/**
 * Graph - received from GraphService
 *
 * GraphState - input of GraphViewComponent, stored in MainComponent
 */
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
type GraphReady = {
  type: 'ready'
  graph: Graph
}
export type GraphState = Empty | Loading | GraphReady

/**
 * Types related to displaying details about currently selected node/edge.
 *
 * SelectedElement - stored in GraphViewComponent, input of EdgeDetailComponent and NodeDetailComponent
 */
export type SelectedEdge = {
  type: 'edge',
  element: Cy.EdgeSingular,
}
export type SelectedNode = {
  type: 'node',
  element: Cy.NodeSingular,
}
export type SelectedElement = Empty | SelectedEdge | SelectedNode

/**
 * Types related to Cytoscape initialization options. The only existing
 * Typescript definition for Cytoscape is far from perfect, so this is a place
 * where they can be amended.
 *
 * Options 'container', 'elements', 'zoom', 'pan' are not covered here.
 *
 * CytoscapeLayout and CytoscapeStyle - stored in GraphViewComponent, inputs of CytoscapeComponent
 *
 * CytoscapeSettings - all other options, stored in GraphViewComponent, controlled by CytoscapeSettingsComponent
 * @see {@link http://js.cytoscape.org/#core/initialisation}
 */
export type CytoscapeLayout = Cy.LayoutOptions & {animationThreshold?: number}
export type CytoscapeStyle = Array<Cy.Stylesheet & {padding?: number}>
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

/**
 * Type of predefined queries in cypher-query.data.ts.
 */
export type PredefinedQuery = {
  name: string
  query: string
}
