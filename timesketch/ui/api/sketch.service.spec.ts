import {TestBed} from '@angular/core/testing';
import {BrowserDynamicTestingModule, platformBrowserDynamicTesting} from '@angular/platform-browser-dynamic/testing';
import {BrowserModule} from '@angular/platform-browser';
import {HttpClientTestingModule, HttpTestingController} from '@angular/common/http/testing';

import {SketchService} from './sketch.service';

describe('SketchService', () => {
  beforeAll(() => {
    TestBed.resetTestEnvironment();
    TestBed.initTestEnvironment(
      BrowserDynamicTestingModule, platformBrowserDynamicTesting(),
    );
  });

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [BrowserModule, HttpClientTestingModule],
      providers: [SketchService],
    });
  });

  describe('.getSketch()', () => {
    it('should return a proper response', async () => {
      const sketchService = TestBed.get(SketchService);
      const http = TestBed.get(HttpTestingController);

      sketchService.sketchId = 42;
      // type is incorrect (typeof 'FAKE_SKETCH' != models.Sketch)
      // but we are only checking that data is just passed as-is from http response
      http.expectOne('/api/v1/sketches/42/').flush({objects: ['FAKE_SKETCH']});

      const sketch = sketchService.sketch;
      expect(sketch).toEqual('FAKE_SKETCH');
      http.verify();
    });
  });

  describe('.search()', () => {
    it('should return a proper response', async () => {
      const sketchService = TestBed.get(SketchService);
      const http = TestBed.get(HttpTestingController);

      sketchService.sketchId = 42;
      http.expectOne('/api/v1/sketches/42/').flush({objects: ['FAKE_SKETCH']});

      const resultsPromise = sketchService.search('FAKE_QUERY').toPromise();
      // type is incorrect (typeof 'FAKE_EVENT' != models.Event)
      // but we are only checking that data is just passed as-is from http response
      http.expectOne('/api/v1/sketches/42/explore/').flush({objects: ['FAKE_EVENT']});

      const results = await resultsPromise;
      expect(results).toEqual(['FAKE_EVENT']);
      http.verify();
    });
  });

  describe('.getEvent()', () => {
    it('should return a proper response', async () => {
      const sketchService = TestBed.get(SketchService);
      const http = TestBed.get(HttpTestingController);

      sketchService.sketchId = 42;
      http.expectOne('/api/v1/sketches/42/').flush({objects: ['FAKE_SKETCH']});

      const eventPromise = sketchService.getEvent('1', '2').toPromise();
      // type is incorrect (typeof 'FAKE_EVENT_DETAIL' != models.EventDetail)
      // but we are only checking that data is just passed as-is from http response
      http
        .expectOne('/api/v1/sketches/42/event/?searchindex_id=1&event_id=2')
        .flush({objects: ['FAKE_EVENT_DETAIL']});

      const event = await eventPromise;
      expect(event).toEqual('FAKE_EVENT_DETAIL');
      http.verify();
    });
  });

  describe('.getTimelineFromIndexName()', () => {
    it('should not throw exceptions when there is no sketch', async () => {
      const sketchService = TestBed.get(SketchService);
      const http = TestBed.get(HttpTestingController);

      expect(sketchService.getTimelineFromIndexName('blah')).toBeNull();
      http.verify();
    });

    it('should not throw exceptions when there is no timeline', async () => {
      const sketchService = TestBed.get(SketchService);
      const http = TestBed.get(HttpTestingController);

      sketchService.sketchId = 42;
      http.expectOne('/api/v1/sketches/42/').flush({objects: [{timelines: []}]});

      expect(sketchService.getTimelineFromIndexName('blah')).toBeNull();
      http.verify();
    });

    it('should return a proper timeline if it exists for given index_name', async () => {
      const sketchService = TestBed.get(SketchService);
      const http = TestBed.get(HttpTestingController);

      sketchService.sketchId = 42;
      http.expectOne('/api/v1/sketches/42/').flush({objects: [{timelines: [
        {name: 'fake_timeline', searchindex: {index_name: 'fake_index'}},
      ]}]});

      expect(sketchService.getTimelineFromIndexName('fake_index')).toEqual({
        name: 'fake_timeline', searchindex: {index_name: 'fake_index'},
      });
      http.verify();
    });
  });
});
