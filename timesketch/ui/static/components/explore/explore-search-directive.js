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

(function() {
    var module = angular.module('timesketch.explore.search.directive', []);

    module.directive('tsSearch', ['$location', 'timesketchApi', function($location, timesketchApi) {
        /**
         * Search the datastore.
         * @param sketch-id - Sketch ID string.
         * @param view-id - Saved view ID string.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-search.html',
            scope: {
                sketchId: '=',
                viewId: '='
            },
            controllerAs: 'ctrl',
            link: function(scope, elem, attrs, ctrl) {
                if (attrs.autoload == 'true') {
                    timesketchApi.getView(attrs.sketchId, attrs.viewId).success(function(data) {
                        var query = data.objects[0].query_string;
                        var filter = angular.fromJson(data.objects[0].query_filter);
                        ctrl.search(query, filter);
                    });
                }
                if (attrs.redirect == 'true') {
                    scope.redirectView = true;
                }
            },
            controller: function($scope) {
                $scope.filter = {"indices": []};

                timesketchApi.getSketch($scope.sketchId).success(function(data) {
                    $scope.sketch = data.objects[0];
                    $scope.sketch.views = data.meta.views;
                    $scope.filter.indices = [];
                        for (var i = 0; i < $scope.sketch.timelines.length; i++) {
                            $scope.filter.indices.push($scope.sketch.timelines[i].searchindex.index_name)
                        }
                });

                this.search = function(query, filter) {
                    if (!filter.order) {
                        filter.order = 'asc';
                    }
                    if (filter.star && query) {
                        filter.star = false;
                    }
                    if (!filter.star && !query) {
                        return
                    }
                    if (filter.time_start) {
                        $scope.showFilters = true;
                    }

                    if (filter.context && query != "*") {
                        delete filter.context;
                    }

                    $scope.events = [];
                    $scope.query = query;
                    $scope.filter = filter;
                    timesketchApi.search($scope.sketchId, query, filter)
                        .success(function(data) {
                            $scope.events = data.objects;
                            $scope.meta = data.meta;
                            if (data.meta.es_total_count > 500) {
                                $scope.meta.noisy = true
                            }
                            $scope.meta.numHiddenEvents = 0;
                    })
                };

                this.aggregation = function(query, filter, aggtype) {
                    timesketchApi.aggregation($scope.sketchId, query, filter, aggtype)
                        .success(function(data) {
                            return data;
                    })
                };

                this.search_starred = function(query, filter) {
                    filter.star = true;
                    query = "";
                    filter.time_start = "";
                    filter.time_end = "";
                    this.search(query, filter)
                };

                this.saveView = function() {
                    timesketchApi.saveView(
                        $scope.sketchId, $scope.view_name, $scope.query, $scope.filter)
                        .success(function(data) {
                            var view_id = data.objects[0].id;
                            var view_url = '/sketch/' + $scope.sketchId + '/explore/view/' + view_id + '/';
                            window.location.href = view_url;
                    });
                };

                this.getContext = function(event) {
                    var new_filter = {};
                    var current_filter = $scope.filter;
                    var current_query = $scope.query;
                    angular.copy(current_filter, new_filter);

                    var context_query = "*";

                    if (!angular.isDefined(new_filter.context)) {
                        new_filter.context = {};
                        new_filter.context.query = current_query;
                        new_filter.context.sketchId = $scope.sketchId;
                        new_filter.context.filter = current_filter;
                        new_filter.context.seconds = 300;
                        new_filter.context.event = {};
                        new_filter.context.meta = {};
                        angular.copy(event, new_filter.context.event);
                        angular.copy($scope.meta, new_filter.context.meta);
                    }

                    angular.copy(event, new_filter.context.event);
                    new_filter.indices = [event._index];
                    new_filter.time_start = moment(event._source.timestamp / 1000).utc().subtract(new_filter.context.seconds, "seconds").format();
                    new_filter.time_end = moment(event._source.timestamp / 1000).utc().add(new_filter.context.seconds, "seconds").format();

                    this.search(context_query, new_filter);
                };

                this.closeContext = function(context) {
                    delete context.filter.context;
                    $scope.showFilters = false;
                    this.search(context.query, context.filter)
                };
            }
        }
    }]);

    module.directive('tsSearchContextCard', function() {
        /**
         * Render the context card.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-search-context-card.html',
            scope: {
                context: '='
            },
            require: '^tsSearch',
            controllerAs: 'ctrl',
            link: function (scope, elem, attrs, ctrl) {
                scope.closeContext = function(context) {
                    ctrl.closeContext(context)
                };
                scope.setInterval = function() {
                    ctrl.getContext(scope.context.event)
                };
            }
        }
    });

    module.directive('tsSearchSavedViewPicker', ['timesketchApi', function(timesketchApi) {
        /**
         * Render the list of saved views.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-search-saved-view-picker.html',
            scope: false,
            link: function (scope, elem, attrs, ctrl) {
                scope.selectedView = {};
                scope.$watch('selectedView.view', function(value) {
                    if (angular.isDefined(scope.selectedView.view)) {
                        if (angular.isDefined(scope.redirectView)) {
                            var view_url = '/sketch/' + scope.sketchId + '/explore/view/' + scope.selectedView.view.id + '/';
                            window.location.href = view_url;
                        } else {
                            timesketchApi.getView(scope.sketchId, scope.selectedView.view.id).success(function(data) {
                                scope.query = data.objects[0].query_string;
                                scope.filter = angular.fromJson(data.objects[0].query_filter);
                                scope.search()
                            });
                        }
                    }
                })
            }
        }
    }]);

})();

