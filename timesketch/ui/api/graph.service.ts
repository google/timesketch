import {Observable} from 'rxjs';
import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';

import {SKETCH_BASE_URL} from './api.service';
import {SketchService} from './sketch.service';

import {
    ElementData,
    GraphDef,
    ElementScratch,
    GraphViews
} from '../graph/models';

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

  search(queryData): Observable<GraphDef> {
    type Dict<T> = {[k: string]: T};

    function object_map<V, W>(obj: Dict<V>, func: (k: string, v: V) => [string, W]): Dict<W> {
      if (! obj) {
        return;
      }
      const parts = Object.entries(obj)
        .map(([k, v]) => func(k, v))
        .map(([k, v]) => ({[k]: v}));
      return Object.assign({}, ...parts);
    }

    function format(formatString: string, params: ElementData): string {
      let result = formatString;
      for (const [k, v] of Object.entries(params)) {
        if (Array.isArray(v)) {
          result = result.replace('{...' + k + '}', v.join(', '));
        } else {
          result = result.replace('{' + k + '}', v);
        }
      }
      return result;
    }

    const element_scratch = (element_schema: ElementScratch, element_data: ElementData): ElementScratch =>
      object_map(element_schema, (k, v): any =>
        typeof v === 'string' ? [k, format(v, element_data)] : [k, v]
      ) as any;

    function format_graph({schema, elements}) {
      const nodes_by_id = {};
      for (const node of elements.nodes) {
        node.scratch = element_scratch(schema.nodes[node.data.type], node.data);
        nodes_by_id[node.data.id] = node;
      }
      for (const edge of elements.edges) {
        const edge_data = {
          ...object_map(nodes_by_id[edge.data.source].data, (k, v) => ['source.' + k, v]),
          ...object_map(nodes_by_id[edge.data.target].data, (k, v) => ['target.' + k, v]),
          ...edge.data,
        };
        edge.scratch = element_scratch(schema.edges[edge.data.type], edge_data);
      }
      return elements;
    }
    return this.http
      .post(`${SKETCH_BASE_URL}${this.sketchService.sketchId}/explore/graph/`, {
        graph_view_id: queryData.id, parameters: queryData.parameters, output_format: 'cytoscape',
      })
      .map((result) => format_graph({
        elements: result['objects'][0]['graph'],
        schema: result['meta']['schema'],
      }));
  }

  getGraphViews(): Observable<GraphViews> {
    return this.http.get(`${SKETCH_BASE_URL}${this.sketchService.sketchId}/explore/graph/views/`, {})
        .map((result) => {
          return result['objects'][0]['views'];
        });
  }

}
