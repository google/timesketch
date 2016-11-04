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
    var module = angular.module('timesketch.explore.event.directive', []);

    module.directive('tsEventList', ['timesketchApi', function(timesketchApi) {
        /**
         * Render list of events (search result from the datastore).
         * @param sketch-id - The id for the sketch.
         * @param meta - Metadata object returned from the datastore search.
         * @param events - Array of events (search results).
         * @param query - Query string for the search results.
         * @param filter - Filter for the search results.
         * @param view-id - ID for the view.
         * @param named-view - Boolean indicating if the view is named.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-event-list.html',
            scope: {
                sketchId: '=',
                meta: '=',
                events: '=',
                query: '=',
                filter: '=',
                queryDsl: '=',
                viewId: '=',
                namedView: '='
            },
            require: '^tsSearch',
            controller: function($scope) {
                if ($scope.namedView) {
                    timesketchApi.getView($scope.sketchId, $scope.viewId).success(function(data) {
                        $scope.view = data.objects[0]
                    });
                }

                var toggleStar = function(event_list) {
                    if (!event_list.length) {return}
                    timesketchApi.saveEventAnnotation(
                        $scope.sketchId,
                        'label',
                        '__ts_star',
                        event_list).success(function (data) {})
                };

                var getSelectedEventsFilter = function() {
                    var event_list = [];
                    var indices_list = [];
                    angular.forEach($scope.events, function(event) {
                        if (event.selected) {
                            indices_list.push(event['_index']);
                            event_list.push(
                                {
                                    "doc_type": event["_type"],
                                    "event_id": event["_id"],
                                    "index": event["_index"]});
                        }
                    });
                    return {"indices": indices_list, "events": event_list};
                };

                $scope.toggleAll = function() {
                    $scope.isAllSelected = $scope.events.every(function(event) {
                        return event.selected;
                    });
                    angular.forEach($scope.events, function(event) {
                        if (!$scope.isAllSelected) {
                            event.selected = true
                        } else {
                            event.selected = false
                        }
                    })
                };

                $scope.saveEventsView = function() {
                    var filter = getSelectedEventsFilter();
                    timesketchApi.saveView(
                        $scope.sketchId, $scope.view_name, false, "", filter, null)
                        .success(function(data) {
                            var view_id = data.objects[0].id;
                            var view_url = '/sketch/' + $scope.sketchId + '/explore/view/' + view_id + '/';
                            window.location.href = view_url;
                        }
                    );
                };

                $scope.updateView = function() {
                    var reload = false;
                    var query = "";
                    var filter = getSelectedEventsFilter();
                    var query_dsl = {};
                    if (filter['events'].length < 1) {
                        query = $scope.query;
                        filter = $scope.filter;
                        query_dsl = $scope.queryDsl
                    } else {
                        reload = true;
                    }
                    timesketchApi.updateView(
                        $scope.sketchId, $scope.viewId, $scope.view.name, query, filter, query_dsl)
                        .success(function(data) {
                            if (reload) {
                                var view_id = data.objects[0].id;
                                var view_url = '/sketch/' + $scope.sketchId + '/explore/view/' + view_id + '/';
                                window.location.href = view_url;
                            }
                        });
                };

                $scope.deleteView = function() {
                    timesketchApi.deleteView($scope.sketchId, $scope.viewId)
                        .success(function(data) {
                            var sketchUrl = '/sketch/' + $scope.sketchId + '/explore/';
                            window.location.href = sketchUrl;
                        });
                };

                $scope.addStar = function() {
                    event_list = [];
                    angular.forEach($scope.events, function(event) {
                        if (event.selected && !event.star) {
                            event.star = true;
                            event_list.push(event);
                        }
                    });
                    toggleStar(event_list)
                };

                $scope.removeStar = function() {
                    event_list = [];
                    angular.forEach($scope.events, function(event) {
                        if (event.selected && event.star) {
                            event.star = false;
                            event_list.push(event);
                        }
                    });
                    toggleStar(event_list)
                };

                $scope.$watch('events', function(value) {
                    if (angular.isDefined(value)) {
                        $scope.anySelected = value.some(function(event) {
                            return event.selected;
                        });
                    }
                }, true)
            },
            link: function(scope, elem, attrs, ctrl) {
                scope.applyOrder = function() {
                    ctrl.search(scope.query, scope.filter);
                };
                scope.$watch('userLimit', function(value) {
                    scope.filter['limit'] = scope.userLimit;
                    ctrl.search(scope.query, scope.filter, scope.queryDsl);
                });
            }
        }
    }]);

    module.directive('tsEvent', function () {
        /**
         * Render event details.
         * @param sketch-id - The id for the sketch.
         * @param meta - Metadata object returned from the datastore search.
         * @param event - Event object.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-event.html',
            scope: {
                sketchId: '=',
                meta: '=',
                event: '=',
                prevTimestamp: '=',
                nextTimestamp: '=',
                index: '=',
                isContextEvent: '=',
                enableContextQuery: '=',
                order: '='
            },
            require: '?^tsSearch',
            controller: function ($scope, timesketchApi) {

                // Calculate the time delta in days between two events.
                var calcDays = function(t1, t2) {
                    var t1_sec = parseInt(t1/1000000);
                    var t2_sec = parseInt(t2/1000000);
                    var delta = parseInt(t1_sec - t2_sec);
                    var delta_days = delta/60/60/24;
                    return parseInt(delta_days)
                };
                if ($scope.index > 0) {
                    var event_timestamp = $scope.event['_source'].timestamp;
                    if ($scope.order == 'asc') {
                        $scope.days = calcDays(event_timestamp, $scope.prevTimestamp)
                    } else {
                        $scope.days = calcDays(event_timestamp, $scope.nextTimestamp)
                    }
                }

                // Get the color and name for the event here to prevent ugly template code.
                $scope.timeline_color = $scope.meta.timeline_colors[$scope.event._index];
                $scope.timeline_name = $scope.meta.timeline_names[$scope.event._index];

                // Defaults to not showing details for the event.
                $scope.showDetails = false;

                $scope.toggleSelected = function() {
                    $scope.event.selected = !$scope.event.selected
                };

                $scope.toggleStar = function() {
                    timesketchApi.saveEventAnnotation(
                        $scope.sketchId,
                        'label',
                        '__ts_star',
                        $scope.event).success(function(data) {})
                };

                $scope.toggleHidden = function() {
                    timesketchApi.saveEventAnnotation(
                        $scope.sketchId,
                        'label',
                        '__ts_hidden',
                        $scope.event).success(function(data) {
                        if ($scope.event.hidden) {
                            $scope.meta.numHiddenEvents++
                        } else {
                            $scope.meta.numHiddenEvents--
                        }
                    })
                };

                $scope.getDetail = function() {
                    if ($scope.eventdetail) {return}
                    timesketchApi.getEvent(
                        $scope.sketchId,
                        $scope.event._index,
                        $scope.event._id).success(function(data) {
                            $scope.eventdetail = data.objects;
                            $scope.comments = data.meta.comments;
                        })
                };

                $scope.postComment = function() {
                    timesketchApi.saveEventAnnotation(
                        $scope.sketchId,
                        'comment',
                        $scope.formData.comment,
                        $scope.event).success(function(data) {
                            $scope.formData.comment = '';
                            $scope.commentForm.$setPristine();
                            $scope.comments.push(data['objects'][0][0]);
                            $scope.comment = true;
                        })
                };

                $scope.$watch('event', function(value) {
                    $scope.star = false;
                    $scope.comment = false;

                    if ($scope.event._source.label.indexOf('__ts_star') > -1) {
                        $scope.event.star = true;
                    } else {
                        $scope.event.star = false;
                    }

                    if ($scope.event._source.label.indexOf('__ts_comment') > -1) {
                        $scope.comment = true;
                    }

                    if ($scope.event._source.label.indexOf('__ts_hidden') > -1) {
                        $scope.event.hidden = true;
                        $scope.meta.numHiddenEvents++;
                    } else {
                        $scope.event.hidden = false;
                    }

                });

            },
            link: function(scope, elem, attrs, ctrl) {
                scope.getContext = function(event) {
                    ctrl.getContext(event);
                }
            }
        }
    });

})();

