/*
Copyright 2015 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
import 'font-awesome/css/font-awesome.css';
import * as $ from 'jquery';
(window as any).jQuery = $;
import 'twitter-bootstrap-3.0.0/dist/css/bootstrap.css';
import 'twitter-bootstrap-3.0.0/dist/js/bootstrap.js';
import 'medium-editor/dist/css/medium-editor.css';
import 'medium-editor/dist/css/themes/default.css';
import 'zone.js';

import angular from 'angularjs-for-webpack';
import {NgModule} from '@angular/core';
import {BrowserModule} from '@angular/platform-browser';
import {FormsModule} from '@angular/forms';
import {HttpClientModule, HTTP_INTERCEPTORS} from '@angular/common/http';

// add all operators from rxjs, don't care about overhead
import 'rxjs/Rx';

// Cytoscape needs that to bind all events
import 'hammerjs';

import './css/ts.scss';

import {tsApiModule} from './api/api.module';
import {AttachCsrfTokenInterceptor} from './api/attach-csrf-token.interceptor';
import {tsCoreModule} from './core/core.module';
import {tsExploreModule} from './explore/explore.module';
import {tsSketchModule, SketchModule} from './sketch/sketch.module';
import {tsStoryModule} from './story/story.module';
import {tsGraphsModule, GraphsModule} from './graphs/graphs.module';

export const tsAppModule = angular.module('timesketch', [
    tsApiModule.name,
    tsCoreModule.name,
    tsExploreModule.name,
    tsSketchModule.name,
    tsStoryModule.name,
    tsGraphsModule.name,
])

.config(function ($httpProvider) {
    // List of URLs to exclude from the butterbar.
    const excludeFromButterbar = (url) => {
      const excludeURLs = [
        '/api/v1/tasks/',
        '/api/v1/sketches/[0-9]+/stories/[0-9]+/',
      ];
      const re = new RegExp(excludeURLs.join('|'), 'i');
      return url.match(re) != null;
    };
    $httpProvider.interceptors.push(function ($q, $rootScope) {
        return {
            'request': function (config) {
                if (!excludeFromButterbar(config.url)) {
                    $rootScope.$broadcast('httpreq-start');
                }
                return config || $q.when(config);
            },
            'response': function (response) {
                $rootScope.XHRError = false;
                $rootScope.$broadcast('httpreq-complete');
                return response || $q.when(response);
            },
            'responseError': function (response) {
                $rootScope.XHRError = response.data;
                $rootScope.$broadcast('httpreq-error');
                return $q.reject(response);
            },
        };
    });
    const csrftoken = document.getElementsByTagName('meta')[0]['content'];
    $httpProvider.defaults.headers.common['X-CSRFToken'] = csrftoken;
});

@NgModule({
  imports: [
    BrowserModule, FormsModule, HttpClientModule,
    SketchModule, GraphsModule,
  ],
  providers: [{
    provide: HTTP_INTERCEPTORS,
    useClass: AttachCsrfTokenInterceptor,
    multi: true,
  }],
})

export class AppModule {
  ngDoBootstrap() {}
}
