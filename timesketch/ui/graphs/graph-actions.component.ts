import {Component, Output, EventEmitter, ElementRef} from '@angular/core'

import {GraphService} from '../api/graph.service'

@Component({
  selector: 'ts-graphs-graph-actions',
  templateUrl: './graph-actions.component.html',
})
export class GraphActionsComponent {
  @Output() actionComplete = new EventEmitter<'delete' | 'regenerate'>()
  regenerationInProgress = false
  deletionInProgress = false

  private _showRegenerationDoneModal = false
  get showRegenerationDoneModal() {return this._showRegenerationDoneModal}
  set showRegenerationDoneModal(value: boolean) {
    if (value) {
      this.elem.nativeElement.style.display = 'block'
    } else {
      this.elem.nativeElement.style.display = ''
    }
    this._showRegenerationDoneModal = value
  }

  private _showDeletionModal = false
  get showDeletionModal() {return this._showDeletionModal}
  set showDeletionModal(value: boolean) {
    if (value) {
      this.elem.nativeElement.style.display = 'block'
    } else {
      this.elem.nativeElement.style.display = ''
    }
    this._showDeletionModal = value
  }

  constructor(
    private readonly graphService: GraphService,
    private readonly elem: ElementRef,
  ) {}

  async regenerateGraph() {
    this.regenerationInProgress = true
    await this.graphService.regenerate().toPromise()
    this.regenerationInProgress = false
    this.showRegenerationDoneModal = true
    this.actionComplete.emit('regenerate')
  }

  async deleteGraph() {
    this.deletionInProgress = true
    await this.graphService.delete().toPromise()
    this.showDeletionModal = false
    this.deletionInProgress = false
    this.actionComplete.emit('delete')
  }
}
