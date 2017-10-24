import {Component, Input, Output, EventEmitter, ChangeDetectorRef} from '@angular/core'
import {GraphState, CytoscapeLayout, SelectedElement} from './models'

import * as data from './graph-view.data'

@Component({
  selector: 'ts-graphs-graph-view',
  templateUrl: './graph-view.component.html',
})
export class GraphViewComponent {
  // tslint:disable-next-line:no-unused-variable
  @Input() state: GraphState
  @Output() invalidate = new EventEmitter<{}>()

  selectedElement: SelectedElement = {type: 'empty'}

  style = data.style
  settings = data.settings

  private _layout = data.layout
  private _null_layout = {name: 'null'}
  get layout(): CytoscapeLayout {
    if (this.state.type === 'ready') {
      return this._layout
    } else {
      return this._null_layout as CytoscapeLayout
    }
  }

  constructor(private readonly changeDetectorRef: ChangeDetectorRef) {}

  initEvents(cy: Cy.Core) {
    cy.on('click', (event) => {
      if (event.target === event.cy) this.selectedElement = {type: 'empty'}
      else if (event.target.isEdge()) this.selectedElement = {type: 'edge', element: event.target}
      else if (event.target.isNode()) this.selectedElement = {type: 'node', element: event.target}
      this.changeDetectorRef.detectChanges()
    })
  }
}
