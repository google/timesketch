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
import * as moment from 'moment'

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
                scope.parseFilterDate(scope.filter.time_start, scope.filter.time_end)
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

            scope.parseFilterDate = function(datevalue, datevalue_end){
                    if (datevalue != null) {
                    var datetimetemplate="YYYY-MM-DDTHH:mm:ss";
                    //Parse out 'T' date time seperator needed by ELK but not by moment.js
                    datevalue=datevalue.replace(/T/g,' ');
                    //Parse offset given by user. Eg. +-10m
                    var offsetRegexp = /(.*?)(-|\+|\+-|-\+)(\d+)(y|d|h|m|s|M|Q|w|ms)/g;
                    var match = offsetRegexp.exec(datevalue);

                    if (match != null) {
                        var filterbase = match[1]
                        var filteroffset = match[2]
                        var filteramount = match[3]
                        var filtertype = match[4]

                        filterbase = moment.utc(filterbase,"YYYY-MM-DD HH:mm:ssZZ");
                        //calculate filter start and end datetimes
                        if (filteroffset == '+') {
                            scope.filter.time_start = moment.utc(filterbase).format(datetimetemplate);
                            scope.filter.time_end = moment.utc(filterbase).add(filteramount,filtertype).format(datetimetemplate);
                        }
                        if (filteroffset == '-') {
                            scope.filter.time_start = moment.utc(filterbase).subtract(filteramount,filtertype).format(datetimetemplate);
                            scope.filter.time_end = moment.utc(filterbase).format(datetimetemplate);
                        }
                        if (filteroffset == '-+' || filteroffset == '+-') {
                            scope.filter.time_start = moment.utc(filterbase).subtract(filteramount,filtertype).format(datetimetemplate);
                            scope.filter.time_end = moment.utc(filterbase).add(filteramount,filtertype).format(datetimetemplate);
                        }
                    } else {
                        if (datevalue_end == null || datevalue_end == '') {
                            scope.filter.time_end = scope.filter.time_start;
                        }
                    }
                }
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
                    scope.timeline_picker_title = {'color': '#D1D1D1'};
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
