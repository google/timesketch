import {Component, Input, OnChanges, SimpleChanges} from '@angular/core'

import {SketchService} from '../api/sketch.service'
import {GraphService} from '../api/graph.service'
import {GraphViewState} from './graph-view.component'

@Component({
  selector: 'ts-graphs-main',
  templateUrl: './main.component.html',
  providers: [SketchService, GraphService],
})
export class MainComponent implements OnChanges {
  @Input() sketchId: string

  graphViewState: GraphViewState = {type: 'empty'}

  constructor(private sketchService: SketchService, private graphService: GraphService) {}

  ngOnChanges(changes: SimpleChanges) {
    this.sketchService.sketchId = Number(this.sketchId)
  }

  onCypherSearch(query: string) {
    this.graphViewState = {type: 'loading'}
    this.graphService.search(query).subscribe((graph) => {
      this.graphViewState = {type: 'ready', graph}
    })
  }
}
