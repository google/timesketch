import {Observable} from 'rxjs'
import {Injectable} from '@angular/core'
import {HttpClient} from '@angular/common/http'

import {SKETCH_BASE_URL} from './api.service'
import {SketchService} from './sketch.service'

/**
 * Service for fetching graph-related API resources.
 * Relevant backend code:
 * @see GraphResource in {@link https://github.com/google/timesketch/blob/master/timesketch/api/v1/resources.py}
 * @see {@link https://github.com/google/timesketch/blob/master/timesketch/lib/datastores/neo4j.py}
 */
@Injectable()
export class GraphService {
  constructor(
    private readonly sketchService: SketchService,
    private readonly http: HttpClient,
  ) {}

  search(query: string): Observable<Cy.ElementsDefinition> {
    return this.http
      .post(`${SKETCH_BASE_URL}${this.sketchService.sketchId}/explore/graph/`, {
        query, output_format: 'cytoscape',
      })
      .map((result) => result['objects'][0]['graph'])
  }
}
