import {Component, Input} from '@angular/core'

/**
 * A subset of Cytoscape initialization options.
 * Does not include the first 6: container, elements, style, layout, zoom, pan.
 * @see {@link http://js.cytoscape.org/#core/initialisation}
 */
export interface CytoscapeSettings {
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

@Component({
  selector: 'ts-graphs-cytoscape-settings',
  templateUrl: './cytoscape-settings.component.html',
})
export class CytoscapeSettingsComponent {
  @Input() settings: CytoscapeSettings
}
