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

var timesketch = angular.module('timesketch', ['timesketch.directives']);

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
    var csrftoken = document.getElementsByTagName('meta')['csrf-token'].getAttribute('content');
    $httpProvider.defaults.headers.common['X-CSRFToken'] = csrftoken;
});

timesketch.controller('ExploreCtrl', function($scope, $http) {
        $scope.init = function(sketch_id, view_id, timelines) {
            $scope.sketch_id = sketch_id;
            $scope.view_id = view_id;
            $scope.timelines = timelines;
            $scope.star = false;
            $scope.filter = {};
            $scope.filter.indices = $scope.timelines.split(",");
            $http.get("/api/v1/sketches/" + $scope.sketch_id + "/views/" + $scope.view_id + "/").success(function(data) {
                $scope.query = data.objects[0].query_string;
                $scope.filter = angular.fromJson(data.objects[0].query_filter);
                if (!$scope.filter.indices) {
                    $scope.filter.indices = timelines.split(",")
                }
                $scope.search();
            });
        };

        $scope.search = function() {
            if ($scope.filter.star && $scope.query) {
                $scope.filter.star = false;
            }
            $scope.noisy = false;
            $scope.events = [];

            if (!$scope.filter.star && !$scope.query) {
                return
            }

            if ($scope.filter.time_start) {
                $scope.showFilters = true;
            }

            var params = {
                params: {
                    q: $scope.query,
                    filter: $scope.filter
                }
            };
            $http.get("/api/v1/sketches/" + $scope.sketch_id + "/explore/", params).success(function(data) {
                $scope.events = data.objects;
                $scope.meta = data.meta;
                if (data.meta.es_total_count > 500) {
                    $scope.noisy = true
                }
            });
        };

        $scope.search_starred = function() {
            $scope.filter.star = true;
            $scope.query = "";
            $scope.filter.time_start = "";
            $scope.filter.time_end = "";
            $scope.search()
        };

        $scope.clearFilter = function() {
            delete $scope.filter.time_start;
            delete $scope.filter.time_end;
            $scope.search()
        };

        $scope.saveView = function() {
            var params = {
                name: $scope.view_name,
                query: $scope.query,
                filter: $scope.filter
            };
            $http.post('/api/v1/sketches/' + $scope.sketch_id + '/views/', params).success(function(data) {
                var id = data.objects[0].id;
                var view_url = '/sketch/' + $scope.sketch_id + '/explore/view/' + id + '/';
                window.location.href = view_url;
            });
        }
});

timesketch.controller('EventCtrl', function($scope, $http) {
    $scope.star = false;

    if ($scope.event._source.label.indexOf('__ts_star') > -1) {
        $scope.star = true;
        $scope.event._source.label.splice($scope.event._source.label.indexOf('__ts_star'), 1)
    }

    if ($scope.event._source.label.indexOf('__ts_comment') > -1) {
        $scope.comment = true;
        $scope.event._source.label.splice($scope.event._source.label.indexOf('__ts_comment'), 1)
    }

    $scope.toggleStar = function() {
        var params = {
            annotation: '__ts_star',
            annotation_type: 'label',
            searchindex_id: $scope.event._index,
            event_id: $scope.event._id
        };
        $http.post('/api/v1/sketches/' + $scope.sketch_id + '/event/annotate/', params).success(function(data) {console.log(data)});
    }
});

timesketch.controller('EventDetailCtrl', function($scope, $http) {
    $scope.formData = {};

    $scope.getDetail = function() {
        var details = {};
        var params = {
            params: {
                searchindex_id: $scope.event._index,
                event_id: $scope.event._id
            }
        };
        $http.get('/api/v1/sketches/' + $scope.sketch_id + '/event/', params).success(function(data) {
            for (var k in data.objects) {
                if (k == '_id' || k == '_index') {
                    continue
                }
                details[k] = data.objects[k]
            }
            $scope.details = details;
            $scope.comments = data.meta.comments
        });
    };

    // Handle comment form submit
    $scope.postComment = function() {
        var params = {
            annotation: $scope.formData.comment,
            annotation_type: 'comment',
            searchindex_id: $scope.event._index,
            event_id: $scope.event._id
        };
        $http.post('/api/v1/sketches/' + $scope.sketch_id + '/event/annotate/', params).success(function(data) {
            $scope.formData.comment = '';
            $scope.commentForm.$setPristine();
            $scope.comments.push(data['objects'][0]);
        });
    };
});
