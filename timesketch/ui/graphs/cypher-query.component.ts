import {Component, EventEmitter, Output} from '@angular/core'

@Component({
  selector: 'ts-graphs-cypher-query',
  templateUrl: './cypher-query.component.html',
})
export class CypherQueryComponent {
  @Output() cypherSearch = new EventEmitter<string>()
  query = 'MATCH (a)-[e]->(b) RETURN *'

  onSubmit() {
    this.cypherSearch.emit(this.query)
  }
}
