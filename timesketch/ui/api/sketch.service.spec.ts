import {TestBed} from '@angular/core/testing'
import {BrowserDynamicTestingModule, platformBrowserDynamicTesting} from '@angular/platform-browser-dynamic/testing'
import {BrowserModule} from '@angular/platform-browser'
import {HttpClientTestingModule, HttpTestingController} from '@angular/common/http/testing'

import {SketchService} from './sketch.service'

describe('SketchService', () => {
  beforeAll(() => {
    TestBed.resetTestEnvironment()
    TestBed.initTestEnvironment(
      BrowserDynamicTestingModule, platformBrowserDynamicTesting(),
    )
  })

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [BrowserModule, HttpClientTestingModule],
      providers: [SketchService],
    })
  })

  describe('.getSketch()', () => {
    it('should return a proper response', async () => {
      const sketchService = TestBed.get(SketchService)
      const http = TestBed.get(HttpTestingController)

      sketchService.sketchId = 42
      const sketchPromise = sketchService.getSketch().toPromise()
      // type is incorrect (typeof 'FAKE_SKETCH' != models.Sketch)
      // but we are only checking that data is just passed as-is from http response
      http.expectOne('/api/v1/sketches/42/').flush({objects: ['FAKE_SKETCH']})

      const sketch = await sketchPromise
      expect(sketch).toEqual('FAKE_SKETCH')
      http.verify()
    })
  })
})
