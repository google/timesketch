import {Component, EventEmitter, Output} from '@angular/core';

import * as data from './cypher-query.data';

@Component({
  selector: 'ts-graphs-cypher-query',
  templateUrl: './cypher-query.component.html',
})
export class CypherQueryComponent {
  @Output() cypherSearch = new EventEmitter<string>();
  query = '';
  predefinedQueries = data.predefinedQueries;

  onQuerySelect(query) {
    this.query = query;
    this.onSubmit();
  }

  onSubmit() {
    this.cypherSearch.emit(this.query);
  }
}
