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
import * as ace from 'brace'
import 'brace/mode/json'
import 'brace/theme/dawn'

export const tsJsonEditor = ['timesketchApi', function(timesketchApi) {
    /**
     * Histogram chart for number of events.
     * @param query - Query string.
     * @param filter - Filter object.
     * @param queryDsl - Query DSL object.
     */
    return {
        restrict: 'E',
        template: require('./json-editor.html'),
        scope: {
            sketchId: '=',
            query: '=',
            filter: '=',
            queryDsl: '='
        },
        require: '^tsSearch',
        link: function(scope, element, attrs, ctrl) {
            const editor = ace.edit("json-editor");
            editor.getSession().setMode("ace/mode/json");
            editor.setTheme("ace/theme/dawn");
            editor.setShowPrintMargin(false);

            timesketchApi.getCurrentQuery(scope.sketchId, scope.query, scope.filter, scope.queryDsl)
                .success(function(data) {
                    let currentQueryDsl = data['objects'][0];
                    // If there is no current query create a generic query.
                    if (!currentQueryDsl) {
                        currentQueryDsl = {
                            "query": {
                                "filtered": {
                                    "query": {
                                        "query_string": {
                                            "query": scope.query}}}},
                            "sort": {
                                "datetime": "asc"}
                        };
                        console.log("use template")
                    }
                    scope.queryDsl = currentQueryDsl;
                    editor.setValue(JSON.stringify(currentQueryDsl, null, '\t'), -1);
                    editor.focus();
                });

            scope.executeQuery = function () {
                scope.queryDsl = editor.getValue();
                ctrl.search(scope.query, scope.filter, scope.queryDsl)
            };

            scope.clearEditor = function () {
                scope.queryDsl = "";
                editor.setValue("");
            }
        }
    }
}]
