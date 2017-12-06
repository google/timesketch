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
      http.expectOne('/api/v1/sketches/42/').flush({objects: ['FAKE_SKETCH']})

      const graphPromise = graphService.search('FAKE_QUERY').toPromise()
      const request = http.expectOne('/api/v1/sketches/42/explore/graph/')

      expect(request.request.body).toEqual({
        query: 'FAKE_QUERY', output_format: 'cytoscape',
      })
      request.flush({
        meta: {schema: {
          nodes: {'Machine': {label: '{hostname} ({...ip_addresses})'}},
          edges: {'ACCESS': {label: '{source.hostname} --{username}--> {target.hostname}'}},
        }},
        objects: [{graph: {
          nodes: [
            {data: {type: 'Machine', id: 'node1', hostname: 'M1', ip_addresses: ['1']}},
            {data: {type: 'Machine', id: 'node2', hostname: 'M2', ip_addresses: ['2', '2', '2']}},
          ],
          edges: [
            {data: {type: 'ACCESS', id: 'edge1', source: 'node1', target: 'node2', username: 'user1'}},
          ],
        }}],
      })

      const graph = await graphPromise
      expect(graph).toEqual({
        nodes: [
          {
            data: {type: 'Machine', id: 'node1', hostname: 'M1', ip_addresses: ['1']},
            scratch: {label: 'M1 (1)'},
          },
          {
            data: {type: 'Machine', id: 'node2', hostname: 'M2', ip_addresses: ['2', '2', '2']},
            scratch: {label: 'M2 (2, 2, 2)'},
          },
        ],
        edges: [
          {
            data: {type: 'ACCESS', id: 'edge1', source: 'node1', target: 'node2', username: 'user1'},
            scratch: {label: 'M1 --user1--> M2'},
          },
        ],
      })
      http.verify()
    })
  })
})
