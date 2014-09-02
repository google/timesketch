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

var timesketch = angular.module('timesketch', ['timesketch.directives', 
    'timesketch.services']);

// config
timesketch.config(function($httpProvider) {
    $httpProvider.interceptors.push(function($q, $rootScope) {
        return {
            'request': function(config) {
                $rootScope.$broadcast('httpreq-start');
                return config || $q.when(config);
            },
            'response': function(response) {
                $rootScope.$broadcast('httpreq-complete');
                return response || $q.when(response);
            }
        };
    });
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});

timesketch.controller('ExploreCtrl', function($scope, $http) {
        $scope.init = function(sketch, view, timelines) {
            $scope.sketch = sketch;
            $scope.star = false;
            $scope.filter = {}
            $scope.filter.indexes = []
            $scope.filter.indexes = timelines.split(",")
            var params = {params: {
                sketch: $scope.sketch,
                view: view
            }}
            if ($scope.filter.indexes.length > 1) {
                $scope.multipleTimelines = true
            }
            $http.get("/api/v1/view/", params).success(function(data) {
                $scope.query = data.objects[0].query;
                $scope.filter = angular.fromJson(data.objects[0].filter);

                if (!$scope.filter.indexes) {
                    $scope.filter.indexes = timelines.split(",")
                }

                if($scope.filter.star) {
                    $scope.search_starred()
                } else {
                    $scope.search();
                }

                if($scope.filter.time_start) {
                    $scope.showFilters = true
                }

            });
        }

        $scope.search = function() {
            if ($scope.filter.star && !$scope.query ) {
                $scope.search_starred()
                return
            }
            $scope.filter.star = false
            $scope.noisy = false
            if (!$scope.query) {
                return
            }
            var params = {params: {
                q: $scope.query,
                sketch: $scope.sketch,
                filter: $scope.filter,
                limit: 500
            }}
            $scope.events = []
            $http.get("/api/v1/search/", params).success(function(data) {
                $scope.events = data.objects;
                $scope.meta = data.meta;
                if (data.meta.es_total_count > 500) {
                    $scope.noisy = true
                }
            });
        }

        $scope.search_starred = function() {
            $scope.filter.star = true;
            $scope.filter.time_start = "";
            $scope.filter.time_end = "";
            $scope.showFilters = false;
            $scope.noisy = false;

            var params = {params: {
                q: "",
                sketch: $scope.sketch,
                filter: $scope.filter,
                limit: 500
            }}
            $scope.events = [];
            $scope.query = "";
            $http.get("/api/v1/search/", params).success(function(data) {
                $scope.events = data.objects;
                $scope.meta = data.meta;
            });
        }

        $scope.clearFilter = function() {
            $scope.filter.time_start = "";
            $scope.filter.time_end = "";
            $scope.search()
        }

        $scope.saveView = function() {
            var params = {data: {
                sketch: $scope.sketch,
                query: $scope.query,
                query_filter: $scope.filter,
                name: $scope.view_name
            }}
            $http.post('/api/v1/view/', params).success(function(data) {});
        }

});

timesketch.controller('EventCtrl', function($scope, $http, AddLabel) {
    $scope.star = false
    if ($scope.event.label.indexOf('__ts_star') > -1) {
        $scope.star = true
        $scope.event.label.splice($scope.event.label.indexOf(
            '__ts_star'), 1)
    }
    if ($scope.event.label.indexOf('__ts_comment') > -1) {
        $scope.comment = true
        $scope.event.label.splice($scope.event.label.indexOf(
            '__ts_comment'), 1)
    }

    $scope.toggleStar = function() {
        var callback = function(response) {}
        AddLabel.post(callback,
            $scope.event.es_index,
            $scope.event.es_id,
            $scope.sketch,
            "__ts_star")
    }
});

timesketch.controller('SketchCtrl', function($scope, $http) {
    $scope.init = function(sketch) {
        $scope.sketch = sketch;
        var params = {params: {
            sketch: $scope.sketch
        }}
    }

    $scope.createSketch = function() {
        var params = {data: {
            title: $scope.sketch.title,
            description: $scope.sketch.description
        }}
        $http.post('/api/v1/sketch/', params).success(
            function(data) {});
    }

    $scope.addTimeline = function() {
        var params = {data: {
            sketch: $scope.sketch,
            timeline: $scope.addtimeline
        }}
        $http.post('/api/v1/sketchtimeline/', params).success(
            function(data) {});
    }
    $scope.setAcl = function() {
        var params = {data: {
            sketch: $scope.sketch,
            sketch_acl: $scope.sketch_acl
        }}
        $http.post('/api/v1/sketch_acl/', params).success(function(data) {});
    }
});

timesketch.controller('EventDetailCtrl', function($scope, $http, AddLabel) {
    $scope.getDetail = function() {
        var details = {}
        var params = {params: {
            index: $scope.event.es_index,
            id: $scope.event.es_id
        }}
        $http.get("/api/v1/event/", params).success(function(data) {
            for (var k in data.objects[0]) {
                if (k == 'es_id' ||k == 'es_index' || k == 'resource_uri') {
                    continue
                }
                details[k] = data.objects[0][k]
            }
            $scope.details = details;
        });
    }

    // Add label form submit
    //$scope.newLabel = {}
    $scope.addLabel = function() {
        var callback = function(response) {
            $scope.newLabel = '';
            $scope.labelForm.$setPristine()
            $scope.event.label.push(response)
        }
        AddLabel.post(callback,
            $scope.event.es_index,
            $scope.event.es_id,
            $scope.sketch,
            $scope.newLabel)
    }
});

timesketch.controller('EventCommentCtrl', function($scope, $http, AddComment) {
    $scope.getComments = function() {
        var params = {params: {
            index: $scope.event.es_index,
            id: $scope.event.es_id,
            sketch: $scope.sketch
        }}
        $http.get("/api/v1/comment/", params).success(function(data) {

            for (var i=0; i<data.objects.length; i++) {
                data.objects[i].created = new Date(data.objects[i].created);
            }
            $scope.comments = data.objects;
        });
    }

    // Handle comment form submit
    $scope.formData = {}
    $scope.submitComment = function() {
        var callback = function(response) {
            $scope.formData.body = '';
            $scope.commentForm.$setPristine()
            console.log(response)
            $scope.comments.push(response)
        }
        AddComment.post(callback,
            $scope.event.es_index,
            $scope.event.es_id,
            $scope.sketch,
            $scope.formData.body)
    }
});
