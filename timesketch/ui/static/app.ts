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
import angular from 'angularjs-for-webpack'

const module = angular.module('timesketch', [
    'timesketch.api',
    'timesketch.core',
    'timesketch.explore',
    'timesketch.sketch',
    'timesketch.story'
]);

// List of URLs to exclude from the butterbar.
function excludeFromButterbar(url) {
    const excludeURLs = [
        "/api/v1/tasks/",
        "/api/v1/sketches/[0-9]+/stories/[0-9]+/"
    ];
    const re = new RegExp(excludeURLs.join("|"), "i");
    return(url.match(re) != null);
}

// Angular config
module.config(function($httpProvider) {
    $httpProvider.interceptors.push(function($q, $rootScope) {
        return {
            'request': function(config) {
                if (!excludeFromButterbar(config.url)) {
                    $rootScope.$broadcast('httpreq-start');
                }
                return config || $q.when(config);
            },
            'response': function(response) {
                $rootScope.XHRError = false;
                $rootScope.$broadcast('httpreq-complete');
                return response || $q.when(response);
            },
            'responseError': function(response) {
                $rootScope.XHRError = response.data;
                $rootScope.$broadcast('httpreq-error');
                return $q.reject(response);
            }
        };
    });
    const csrftoken = document.getElementsByTagName('meta')[0]['content'];
    $httpProvider.defaults.headers.common['X-CSRFToken'] = csrftoken;
});
