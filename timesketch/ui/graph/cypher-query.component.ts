import {
    Component,
    EventEmitter,
    Input,
    OnChanges,
    SimpleChanges,
    Output
} from '@angular/core';

import {GraphService} from "../api/graph.service";

@Component({
    selector: 'ts-graphs-cypher-query',
    templateUrl: './cypher-query.component.html',
    providers: [GraphService]
})
export class CypherQueryComponent implements OnChanges {
  @Input() sketchId: number;
  @Output() cypherSearch = new EventEmitter<string>();

  graph_view_id: string;
  predefinedQueries = null;

  constructor(
    private readonly graphService: GraphService,
  ) {}

  ngOnChanges(changes: SimpleChanges) {
    if (this.sketchId) {
      this.graphService.getGraphViews().subscribe((result) => {
        this.predefinedQueries = result;
      })
    }
  }

  onQuerySelect(graph_view_id) {
    this.graph_view_id = graph_view_id;
    this.onSubmit();
  }

  onSubmit() {
    this.cypherSearch.emit(this.graph_view_id);
  }
}
