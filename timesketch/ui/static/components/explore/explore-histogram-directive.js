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
    var module = angular.module('timesketch.explore.histogram.directive', []);

    module.directive('tsHistogram', function ($window, timesketchApi) {
        /**
         * Histogram chart for number of events.
         * @param sketchId - Sketch ID.
         * @param filter - Filter object.
         * @param query - Query string.
         * @param meta - Events metadata object.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-histogram.html',
            scope: {
                sketchId: '=',
                filter: '=',
                query: '=',
                meta: '=',
                showCharts: '='
            },
            require: '^tsSearch',
            link: function(scope, element, attrs, ctrl) {

                scope.$watchGroup(['meta', 'showCharts'], function (newval, oldval) {
                    if(scope.showCharts) {
                        timesketchApi.aggregation(scope.sketchId, scope.query, scope.filter, 'histogram')
                            .success(function(data) {
                                scope.render_histogram(data['objects'])
                            });
                    }
                }, true);

                scope.render_histogram = function(data) {
                    if (scope.histogram) {
                        scope.histogram.destroy();
                    }
                    var label_array = [];
                    var data_array = [];

                    data.forEach(function (d) {
                        label_array.push(d.key_as_string);
                        data_array.push(d.doc_count);
                    });
                    
                    var ctx = document.getElementById("histogram");
                    scope.histogram = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: label_array,
                            datasets: [{
                                label: 'events',
                                data: data_array,
                                backgroundColor: '#428bca',
                                borderWidth: 0
                            }]
                        },
                        options: {
                            legend: {
                                display: false
                            },
                            scales: {
                                yAxes: [{
                                    gridLines: {
                                        display: false
                                    },
                                    type: 'logarithmic',
                                    ticks: {
                                        beginAtZero:true
                                    }
                                }],
                                xAxes: [{
                                    type: 'time',
                                    gridLines: {
                                        display: false
                                    }
                                }]

                            }
                        }
                    });
                };
            }
        }
    });
})();
