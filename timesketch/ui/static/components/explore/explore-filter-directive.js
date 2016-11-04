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
    var module = angular.module('timesketch.explore.filter.directive', []);

    module.directive('tsFilter', function () {
        /**
         * Manage query filters.
         * @param sketch - Sketch object.
         * @param filter - Filter object.
         * @param query - Query string.
         * @param queryDsl - Query DSL JSON string.
         * @param show-filters - Boolean value. If set to true the filter card will be shown.
         * @param events - Array of events objects.
         * @param meta - Events metadata object.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-filter.html',
            scope: {
                sketch: '=',
                filter: '=',
                query: '=',
                queryDsl: '=',
                showFilters: '=',
                events: '=',
                meta: '='
            },
            require: '^tsSearch',
            link: function(scope, elem, attrs, ctrl) {
                scope.applyFilter = function() {
                    ctrl.search(scope.query, scope.filter, scope.queryDsl)
                };

                scope.clearFilter = function() {
                    delete scope.filter.time_start;
                    delete scope.filter.time_end;
                    scope.showFilters = false;
                    ctrl.search(scope.query, scope.filter, scope.queryDsl)
                };

                scope.enableAllTimelines = function() {
                    scope.filter.indices = [];
                    for (var i = 0; i < scope.sketch.timelines.length; i++) {
                        scope.filter.indices.push(scope.sketch.timelines[i].searchindex.index_name)
                    }
                    ctrl.search(scope.query, scope.filter, scope.queryDsl)
                };
                scope.disableAllTimelines = function() {
                    scope.filter.indices = [];
                    scope.events = [];
                    scope.meta.es_total_count = 0;
                    scope.meta.es_time = 0;
                    scope.meta.noisy = false;
                }

            }
        }
    });

    module.directive('tsTimelinePickerItem', function() {
        /**
         * Manage the timeline items to filter on.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-timeline-picker-item.html',
            scope: {
                timeline: '=',
                query: '=',
                queryDsl: '=',
                filter: '='
            },
            require: '^tsSearch',
            link: function(scope, elem, attrs, ctrl) {
                scope.checkboxModel = {};
                var index_name = scope.timeline.searchindex.index_name;
                scope.toggleCheckbox = function () {
                    var index = scope.filter.indices.indexOf(index_name);
                    scope.checkboxModel.active = !scope.checkboxModel.active;
                    if (!scope.checkboxModel.active) {
                        if (index > -1) {
                            scope.filter.indices.splice(index, 1);
                        }
                    } else {
                        if (index == -1) {
                            scope.filter.indices.push(index_name);
                        }
                    }
                    ctrl.search(scope.query, scope.filter, scope.queryDsl);
                };
                scope.$watch("filter.indices", function(value) {
                    if (scope.filter.indices.indexOf(index_name) == -1) {
                        scope.colorbox = {'background-color': '#E9E9E9'};
                        scope.timeline_picker_title = {'color': '#D1D1D1', 'text-decoration': 'line-through'};
                        scope.checkboxModel.active = false;
                    } else {
                        scope.colorbox = {'background-color': "#" + scope.timeline.color};
                        scope.timeline_picker_title = {'color': '#333', 'text-decoration': 'none'};
                        scope.checkboxModel.active = true;
                    }
                }, true);
            }
        }
    });

    module.directive('tsDataTypePickerItem', function() {
        /**
         * Manage the data types items to filter on.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-data-type-picker-item.html',
            scope: {
                datatype: '=',
                query: '=',
                queryDsl: '=',
                meta: '=',
                filter: '='
            },
            require: '^tsSearch',
            link: function(scope, elem, attrs, ctrl) {
                scope.checkboxModel = {};
                scope.checkboxModel.active = true;

                if (!scope.filter.exclude) {
                    scope.filter.exclude = [];
                } else {
                    var index = scope.filter.exclude.indexOf(scope.datatype.key);
                    if (index > -1) {
                        scope.checkboxModel.active = false;
                    }
                }

                scope.toggleCheckbox = function () {
                    var index = scope.filter.exclude.indexOf(scope.datatype.key);
                    scope.checkboxModel.active = !scope.checkboxModel.active;

                    if (scope.checkboxModel.active) {
                        if (index > -1) {
                            scope.filter.exclude.splice(index, 1);
                            scope.datatype_picker_title = {'color': '#333', 'text-decoration': 'none'};
                            scope.datatype_picker_color = {'color': '#333', 'background': '#428bca'};
                        }
                    } else {
                        if (index == -1) {
                            scope.filter.exclude.push(scope.datatype.key);
                            scope.datatype_picker_title = {'color': '#D1D1D1', 'text-decoration': 'line-through'};
                            scope.datatype_picker_color = {'color': '#D1D1D1', 'background': '#D1D1D1'};
                        }
                    }
                    ctrl.search(scope.query, scope.filter, scope.queryDsl);
                };
                scope.$watch("filter", function(value) {
                    if (scope.filter.exclude.indexOf(scope.datatype.key) == -1) {
                        scope.datatype_picker_title = {'color': '#333', 'text-decoration': 'none'};
                        scope.datatype_picker_color = {'color': '#333', 'background': '#428bca'};
                    } else {
                        scope.datatype_picker_title = {'color': '#D1D1D1', 'text-decoration': 'line-through'};
                        scope.datatype_picker_color = {'color': '#D1D1D1', 'background': '#D1D1D1'};
                    }
                }, true);
            }
        }
    });


})();
