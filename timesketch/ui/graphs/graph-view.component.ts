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

  showSidebar = false

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

  showNeighborhood(event) {
    let neighborhoodCollection = event.cy.collection()
    const selectedElements = event.cy.filter(':selected')

    if (!selectedElements.length) {
      event.cy.elements().removeClass('faded')
      return
    }

    selectedElements.forEach(function (element) {
      if (element.isNode()) {
        neighborhoodCollection = neighborhoodCollection.add(element.neighborhood().add(element))
      } else if (element.isEdge()) {
        neighborhoodCollection = neighborhoodCollection.add(element.connectedNodes().add(element))
      }
    })

    event.cy.elements().addClass('faded')
    neighborhoodCollection.removeClass('faded')
  }

  unSelectAllElements(event) {
    event.cy.elements().unselect()
    this.selectedElement = {type: 'empty'}
  }

  initEvents(cy: Cy.Core) {
    cy.on('tap', (event) => {
      if (event.target === event.cy) this.selectedElement = {type: 'empty'}
      else if (event.target.isEdge()) this.selectedElement = {type: 'edge', element: event.target}
      else if (event.target.isNode()) this.selectedElement = {type: 'node', element: event.target}
      this.changeDetectorRef.detectChanges()
    })

    // Fade all elements except selected elements and their immidiate neighbors.
    cy.on('select unselect', (event) => {
      this.showNeighborhood(event)
    })
    // Unselect all elements if user click on canvas.
    cy.on('tap', (event) => {
      if (event.target === event.cy) {
        this.unSelectAllElements(event)
      }
    })
    // Unselect all elements when layout is starting otherwise there can be
    // selected elements left between Cypher queries.
    cy.on('layoutstart', (event) => {
      this.unSelectAllElements(event)
    })

  }

}
