import {Component, Input} from '@angular/core'

import {SelectedNode} from './models'

@Component({
  selector: 'ts-graphs-node-detail',
  templateUrl: './node-detail.component.html',
})
export class NodeDetailComponent {
  @Input() selectedNode: SelectedNode
}
