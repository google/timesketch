import {Component, Input} from '@angular/core'

import {CytoscapeSettings} from './models'

@Component({
  selector: 'ts-graphs-cytoscape-settings',
  templateUrl: './cytoscape-settings.component.html',
})
export class CytoscapeSettingsComponent {
  @Input() settings: CytoscapeSettings
}
