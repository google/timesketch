import {Component, EventEmitter, Output} from '@angular/core'

@Component({
  selector: 'ts-graphs-cypher-query',
  templateUrl: './cypher-query.component.html',
})
export class CypherQueryComponent {
  @Output() cypherSearch = new EventEmitter<string>()
  query = ''

  predefinedQueries = [
    {
      name:'Interactive logins',
      query:'MATCH (user:WindowsADUser)-[r1:ACCESS]->(m1:WindowsMachine) WHERE r1.method = "Interactive" RETURN *'
    },
    {
      name:'Entire graph',
      query:'MATCH (a)-[e]->(b) RETURN *'
    }
  ];

  onQuerySelect(query) {
    this.query = query
    this.onSubmit()
  }

  onSubmit() {
    this.cypherSearch.emit(this.query)
  }

}
