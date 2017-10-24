import {Observable} from 'rxjs'
import {Injectable} from '@angular/core'
import {HttpClient} from '@angular/common/http'

import {SKETCH_BASE_URL} from './api.service'
import {SketchService} from './sketch.service'

import {ElementData, GraphDef, ElementScratch} from '../graphs/models'

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

  search(query: string): Observable<GraphDef> {
    function format(formatString: string, params: ElementData): string {
      let result = formatString
      for (const [k, v] of Object.entries(params)) {
        if (Array.isArray(v)) {
          result = result.replace('{...' + k + '}', v.join(', '))
        } else {
          result = result.replace('{' + k + '}', v)
        }
      }
      return result
    }
    function element_scratch(element_schema: ElementScratch, element_data: ElementData): ElementScratch {
      function transform([k, v]: [keyof ElementScratch, ElementScratch[keyof ElementScratch]]) {
        if (typeof v === 'string') {
          return {[k]: format(v, element_data)}
        } else {
          return {[k]: v}
        }
      }
      return Object.assign({}, ...Object.entries(element_schema).map(transform))
    }
    function format_graph({schema, elements}) {
      for (const node of elements.nodes) {
        node.scratch = element_scratch(schema.nodes[node.data.type], node.data)
      }
      for (const edge of elements.edges) {
        edge.scratch = element_scratch(schema.edges[edge.data.type], edge.data)
      }
      return elements
    }
    return this.http
      .post(`${SKETCH_BASE_URL}${this.sketchService.sketchId}/explore/graph/`, {
        query, output_format: 'cytoscape',
      })
      .map((result) => format_graph({
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
