/*
Copyright 2014 Google Inc. All rights reserved.

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

var services = angular.module('timesketch.services', []);

services.factory('AddComment', function($http) {
    var AddComment = {};
    AddComment.post = function(callback, index, id, sketch, body) {
        $http.post('/api/v1/comment/', {data: {
            index: index,
            id: id,
            sketch: sketch,
            body: body}}).success(function(response) {
                callback(response.data);
            });
    };
    return AddComment;
});

services.factory('AddLabel', function($http) {
    console.log("in service")
    var AddLabel = {};
    AddLabel.post = function(callback, index, id, sketch, label) {
        $http.post('/api/v1/label/', {data: {
            index: index,
            id: id,
            sketch: sketch,
            label: label}}).success(function(response) {
                callback(response.data.label);
            });
    };
    return AddLabel;
});
