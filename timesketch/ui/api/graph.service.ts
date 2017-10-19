import {Observable} from 'rxjs'
import {Injectable} from '@angular/core'
import {HttpClient} from '@angular/common/http'

import {SKETCH_BASE_URL} from './api.service'
import {SketchService} from './sketch.service'

export type Graph = {
  elements: Cy.ElementsDefinition
  schema: {
    nodes: {[type: string]: {
      label_template: string
    }}
    edges: {[type: string]: {
      label_template: string
    }}
  }
}

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

  search(query: string): Observable<Graph> {
    return this.http
      .post(`${SKETCH_BASE_URL}${this.sketchService.sketchId}/explore/graph/`, {
        query, output_format: 'cytoscape',
      })
      .map((result) => ({
        elements: result['objects'][0]['graph'],
        schema: result['meta']['schema'],
      }))
  }
  regenerate(): Observable<{}> {
    return this.http
      .post(`/api/experimental/sketches/${this.sketchService.sketchId}/create_graph/`, {})
      .map(() => ({}))
  }
  delete(): Observable<{}> {
    return this.http
      .post(`/api/experimental/sketches/${this.sketchService.sketchId}/delete_graph/`, {})
      .map(() => ({}))
  }
}
