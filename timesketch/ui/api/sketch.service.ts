import {Observable} from 'rxjs'
import {Injectable} from '@angular/core'
import {HttpClient} from '@angular/common/http'

import {SKETCH_BASE_URL} from './api.service'
import {Sketch} from './models'

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
  sketchId: number

  constructor(private http: HttpClient) {}

  getSketch(): Observable<Sketch> {
    return this.http
      .get(`${SKETCH_BASE_URL}${this.sketchId}/`)
      .map((response) => response['objects'][0])
  }
}
