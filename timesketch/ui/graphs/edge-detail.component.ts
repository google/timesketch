import {Component, Input} from '@angular/core'

import {SelectedEdge} from './models'

@Component({
  selector: 'ts-graphs-edge-detail',
  templateUrl: './edge-detail.component.html',
})
export class EdgeDetailComponent {
  @Input() selectedEdge: SelectedEdge
}
