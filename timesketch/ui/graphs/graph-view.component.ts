import {Component, Input, Output, EventEmitter} from '@angular/core'

import {GraphState, CytoscapeLayout} from './models'

import * as data from './graph-view.data'

function format(formatString: string, params: {[k: string]: string}): string {
  let result = formatString
  for (const [k, v] of Object.entries(params)) {
    result = result.replace('{' + k + '}', v)
  }
  return result
}

@Component({
  selector: 'ts-graphs-graph-view',
  templateUrl: './graph-view.component.html',
})
export class GraphViewComponent {
  // tslint:disable-next-line:no-unused-variable
  @Input() state: GraphState
  @Output() invalidate = new EventEmitter<{}>()

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

  nodeLabel = (node_data) => {
    if (this.state.type === 'ready') {
      const {label_template} = this.state.graph.schema.nodes[node_data.type]
      return format(label_template, node_data)
    } else {
      return ''
    }
  }
  edgeLabel = (edge_data) => {
    if (this.state.type === 'ready') {
      const {label_template} = this.state.graph.schema.edges[edge_data.type]
      return format(label_template, edge_data)
    } else {
      return ''
    }
  }
  style = data.style({
    nodeLabel: this.nodeLabel,
    edgeLabel: this.edgeLabel,
  })
}
