import {Observable} from 'rxjs';
import {Injectable} from '@angular/core';
import {HttpClient, HttpParams} from '@angular/common/http';

import {SKETCH_BASE_URL} from './api.service';
import {Sketch, Timeline} from './models';
import {Event, EventDetail} from '../graphs/models';

/**
 * A service that is intended to gather most of the resources defined in
 * @see {@link https://github.com/google/timesketch/blob/master/timesketch/api/v1/resources.py}
 * For convenience, this service stores sketch id as a property. Each method
 * implicitly operates in context of this particular sketch. It is intended
 * that a root component provides this service to other components and is
 * responsible for setting {@link SketchService#sketchId}. Functionality that is
 * linked to a sketch but is conceptually separate should be placed in other
 * services that depend on SketchService, such as GraphService. These services
 * should also implicitly operate in context of the sketch pointed to by
 * {@link SketchService#sketchId}.
 */
@Injectable()
export class SketchService {
  private _sketchId: number;
  public sketch: Sketch;

  get sketchId(): number {
    return this._sketchId;
  }

  set sketchId(id: number) {
    this._sketchId = id;
    this.getSketch().subscribe((sketch) => {
      this.sketch = sketch;
    });
  }

  constructor(private http: HttpClient) {}

  private getSketch(): Observable<Sketch> {
    return this.http
      .get(`${SKETCH_BASE_URL}${this.sketchId}/`)
      .map((response) => response['objects'][0]);
  }

  search(query: string): Observable<Event[]> {
    return this.http
      .post(`${SKETCH_BASE_URL}${this.sketchId}/explore/`, {
        query, filter: {size: 100, from: 0}, dsl: {},
      })
      .map((result) => result['objects']);
  }

  getEvent(searchindex_id: string, event_id: string): Observable<EventDetail> {
    const params = new HttpParams()
      .append('searchindex_id', searchindex_id)
      .append('event_id', event_id)
      .toString();
    return this.http
      .get(`${SKETCH_BASE_URL}${this.sketchId}/event/?${params}`)
      .map((result) => result['objects'][0]);
  }

  getTimelineFromIndexName(index_name: string): Timeline {
    if (!this.sketch) return null;
    for (const timeline of this.sketch.timelines) {
      if (timeline.searchindex.index_name === index_name) return timeline;
    }
    return null;
  }
}
