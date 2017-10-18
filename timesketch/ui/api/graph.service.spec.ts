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
      // types are incorrect (for example, typeof 'FAKE_ELEMENTS' != Cy.ElementsDefinition)
      // but we are only checking that data is just passed as-is from http response
      request.flush({meta: {schema: 'FAKE_SCHEMA'}, objects: [{graph: 'FAKE_ELEMENTS'}]})

      const graph = await graphPromise
      expect(graph).toEqual({elements: 'FAKE_ELEMENTS', schema: 'FAKE_SCHEMA'})
      http.verify()
    })
  })
})
