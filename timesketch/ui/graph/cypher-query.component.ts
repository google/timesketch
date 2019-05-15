import {
    Component,
    EventEmitter,
    Input,
    OnChanges,
    SimpleChanges,
    Output
} from '@angular/core';

import {GraphService} from '../api/graph.service';

@Component({
    selector: 'ts-graphs-cypher-query',
    templateUrl: './cypher-query.component.html',
    providers: [GraphService],
})
export class CypherQueryComponent implements OnChanges {
  @Input() sketchId: number;
  @Output() cypherSearch = new EventEmitter<string>();

  predefinedQueries;
  selectedQuery;

  constructor(
    private readonly graphService: GraphService,
  ) {}

  ngOnChanges(changes: SimpleChanges) {
    if (this.sketchId) {
      this.graphService.getGraphViews().subscribe((result) => {
        this.predefinedQueries = result;
      });
    }
  }

  onQuerySelect(query) {
      this.selectedQuery = this.predefinedQueries[query];
  }

  onQuerySubmit(queryData) {
      this.cypherSearch.emit(queryData);
  }

}
