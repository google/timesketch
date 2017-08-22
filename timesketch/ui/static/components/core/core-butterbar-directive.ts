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
import angular from 'angular'

(function() {
    var module = angular.module('timesketch.core.butterbar.directive', []);

    module.directive('tsButterbar', ['$rootScope', function($rootScope) {
        /**
         * Render (show/hide) the butterbar when AJAX calls are being made.
         */
        return {
            restrict : "A",
            scope: {},
            link : function(scope, element, attrs) {
                scope.$on("httpreq-start", function(e) {
                    element.text("Loading..");
                    element.css({"display": "block"});
                });

                scope.$on("httpreq-error", function(e) {
                    element.css({"display": "block"});
                    element.text($rootScope.XHRError.message || "Error")
                });

                scope.$on("httpreq-complete", function(e) {
                    element.css({"display": "none"});
                });
            }
        };
    }]);
})();
