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

'use strict';

var module = angular.module('timesketch.services', []);

var timesketchApiImplementation = function($http) {
    var base_url = '/api/v1/sketches/';

    this.getView = function(sketch_id, view_id) {
        var resource_url = base_url + sketch_id + '/views/' + view_id;
        return $http.get(resource_url)
    };

    this.saveView = function(sketch_id, name, query, filter) {
        var resource_url = base_url + sketch_id + '/views/';
        var params = {
            name: name,
            query: query,
            filter: filter
        };
        return $http.post(resource_url, params)
    };

    this.getEvent = function(sketch_id, searchindex_id, event_id) {
        var resource_url = base_url + sketch_id + '/event/';
        var params = {
            params: {
                searchindex_id: searchindex_id,
                event_id: event_id
            }
        };
        return $http.get(resource_url, params)
    };

    this.search = function(sketch_id, query, filter) {
        var resource_url = base_url + sketch_id + '/explore/';
        var params = {
            params: {
                q: query,
                filter: filter
            }
        };
        return $http.get(resource_url, params)
    };

    this.addEventAnnotation = function(
        sketch_id, type, annotation, searchindex_id, event_id) {
            var resource_url = base_url + sketch_id + '/event/annotate/';
            var params = {
                annotation: annotation,
                annotation_type: type,
                searchindex_id: searchindex_id,
                event_id: event_id
            };
            return $http.post(resource_url, params);
    };
};

module.service('timesketchApi', timesketchApiImplementation);