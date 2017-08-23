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

(function() {
    var module = angular.module('timesketch.sketch.timelines.directive', []);

    module.directive('tsTimelinesList', ['timesketchApi', function (timesketchApi) {
        /**
         * Render the list of timelines.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/sketch/sketch-timelines-list.html',
            scope: {
                sketchId: '=',
                showEdit: '=',
                showDelete: '='
            },
            controller: function ($scope) {
                timesketchApi.getTimelines($scope.sketchId).success(function (data) {
                    $scope.timelines = [];
                    var timelines = data.objects[0];
                    if (timelines) {
                        for (var i = 0; i < timelines.length; i++) {
                            var timeline = timelines[i];
                            timeline.updated_at = moment.utc(timeline.updated_at).format("YYYY-MM-DD");
                            $scope.timelines.push(timeline)
                        }
                    }
                });

                $scope.deleteTimeline = function(timeline) {
                    timesketchApi.deleteTimeline($scope.sketchId, timeline.id);
                    var index = $scope.timelines.indexOf(timeline);
                    if (index > -1) {
                        $scope.timelines.splice(index, 1);
                    }
                };

                this.updateTimelines = function(timeline) {
                    $scope.timelines.unshift(timeline)
                }
            }
        }
    }]);

})();
