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
import * as numeral from 'numeral/numeral.js'

var module = angular.module('timesketch.sketch.count.events.directive', []);

module.directive('tsCountEvents', ['timesketchApi', function (timesketchApi) {
    /**
     * Render event count.
     */
    return {
        restrict: 'E',
        templateUrl: '/static/components/sketch/sketch-count-events.html',
        scope: {
            sketchId: '='
        },
        controller: function ($scope) {
            timesketchApi.countEvents($scope.sketchId).success(function (data) {
                $scope.count = numeral(data.meta['count']).format('0.0a');
            });
        }
    }
}]);
