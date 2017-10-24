import {Component, Input} from '@angular/core'

import {ElementScratch} from './models'

@Component({
  selector: 'ts-graphs-sidebar',
  templateUrl: './sidebar.component.html',
})
export class SidebarComponent {
  @Input() element: Cy.SingularElement

  get scratch(): ElementScratch {
    return this.element.scratch()
  }

  get type(): string {
    return this.element.data().type
  }

  get es_query(): string {
    return this.element.scratch().es_query
  }

  get data_rows(): Array<{key: string, value: string}> {
    return Object
      .entries(this.element.data())
      .map(([key, value]) => ({key, value}))
      .filter(({key, value}) =>
        this.scratch.hidden_fields.indexOf(key) === -1
      )
      .map(({key, value}) => {
        if (Array.isArray(value)) return {key, value: value.join(', ')}
        return {key, value}
      })
  }
}
