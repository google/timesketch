import {Component, Input, OnChanges, SimpleChanges} from '@angular/core';

import {SketchService} from '../api/sketch.service';
import {GraphService} from '../api/graph.service';
import {GraphState} from './models';

@Component({
  selector: 'ts-graphs-main',
  templateUrl: './main.component.html',
  providers: [SketchService, GraphService],
})

export class MainComponent implements OnChanges {
  @Input() sketchId: string;

  graphState: GraphState = {type: 'empty'};

  constructor(
    private readonly sketchService: SketchService,
    private readonly graphService: GraphService,
  ) {}

  ngOnChanges(changes: SimpleChanges) {
    this.sketchService.sketchId = Number(this.sketchId);
  }

  onCypherSearch(query: string) {
    this.graphState = {type: 'loading'};
    this.graphService.search(query).subscribe((elements) => {
      this.graphState = {type: 'ready', elements};
    });
  }

  onInvalidate() {
    this.graphState = {type: 'empty'};
  }
}
