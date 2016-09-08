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
    var module = angular.module('timesketch.explore.json.editor.directive', []);

    module.directive('tsJsonEditor', function() {
        /**
         * Histogram chart for number of events.
         * @param query - Query string.
         * @param filter - Filter object.
         * @param queryDsl - Query DSL object.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-json-editor.html',
            scope: {
                query: '=',
                filter: '=',
                queryDsl: '='
            },
            require: '^tsSearch',
            link: function(scope, element, attrs, ctrl) {
                var editor = ace.edit("json-editor");
                editor.getSession().setMode("ace/mode/json");
                editor.setTheme("ace/theme/dawn");
                editor.setShowPrintMargin(false);

                if (!scope.queryDsl) {
                    var template_query = {"query": {"filtered": {"query": {"query_string": {"query": scope.query}}}},"sort": {"datetime": "asc"}};
                    editor.setValue(JSON.stringify(template_query, null, '\t'), -1);
                } else {
                    editor.setValue(scope.queryDsl, -1);
                }
                editor.focus();

                scope.execute_query = function () {
                    ctrl.search(scope.query, scope.filter, editor.getValue())
                };

                scope.clear_editor = function () {
                    editor.setValue("");
                }
            }
        }
    });
})();
