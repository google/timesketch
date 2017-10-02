import {TestBed} from '@angular/core/testing'
import {BrowserDynamicTestingModule, platformBrowserDynamicTesting} from '@angular/platform-browser-dynamic/testing'
import {BrowserModule} from '@angular/platform-browser'
import {HttpClientTestingModule, HttpTestingController} from '@angular/common/http/testing'

import {GraphService} from './graph.service'
import {SketchService} from './sketch.service'

describe('GraphService', () => {
  beforeAll(() => {
    TestBed.resetTestEnvironment()
    TestBed.initTestEnvironment(
      BrowserDynamicTestingModule, platformBrowserDynamicTesting(),
    )
  })

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [BrowserModule, HttpClientTestingModule],
      providers: [SketchService, GraphService],
    })
  })

  describe('.search()', () => {
    it('should return a proper response for a query', async () => {
      const sketchService = TestBed.get(SketchService)
      const graphService = TestBed.get(GraphService)
      const http = TestBed.get(HttpTestingController)

      sketchService.sketchId = 42
      const graphPromise = graphService.search('FAKE_QUERY').toPromise()
      const request = http.expectOne('/api/v1/sketches/42/explore/graph/')

      expect(request.request.body).toEqual({
        query: 'FAKE_QUERY', output_format: 'cytoscape',
      })
      // type is incorrect (typeof 'FAKE_GRAPH' != Cy.ElementsDefinition)
      // but we are only checking that data is just passed as-is from http response
      request.flush({objects: [{graph: 'FAKE_GRAPH'}]})

      const graph = await graphPromise
      expect(graph).toEqual('FAKE_GRAPH')
      http.verify()
    })
  })
})
