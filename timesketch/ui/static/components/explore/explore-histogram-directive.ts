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
import {Chart} from 'chart.js'

(function() {
    var module = angular.module('timesketch.explore.histogram.directive', []);

    module.directive('tsHistogram', function ($window, timesketchApi) {
        /**
         * Histogram chart for number of events.
         * @param sketchId - Sketch ID.
         * @param filter - Filter object.
         * @param query - Query string.
         * @param queryDsl - Query DSL JSON string.
         * @param meta - Events metadata object.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/explore/explore-histogram.html',
            scope: {
                sketchId: '=',
                filter: '=',
                query: '=',
                queryDsl: '=',
                meta: '=',
                showCharts: '='
            },
            require: '^tsSearch',
            link: function(scope, element, attrs, ctrl) {

                // Default chart type
                scope.chartType = "bar";

                scope.$watchGroup(['meta', 'showCharts', 'chartType'], function (newval, oldval) {
                    if(scope.showCharts) {
                        timesketchApi.aggregation(scope.sketchId, scope.query, scope.filter, scope.queryDsl, 'histogram')
                            .success(function(data) {
                                render_histogram(data['objects'])
                            });
                    }
                }, true);

                scope.toggleChartType = function () {
                  if (scope.chartType == 'bar') {
                      scope.chartType = 'line';
                  } else {
                      scope.chartType = 'bar';
                  }
                };

                function render_histogram(aggregation) {
                    // Remove the current histogram canvas to avoid old data
                    // to be rendered.
                    if (scope.histogram) {
                        scope.histogram.destroy();
                    }

                    // Arrays to hold out chart data.
                    var chart_labels: any[] = [];
                    var chart_values: any[] = [];

                    aggregation.forEach(function (d) {
                        chart_labels.push(d.key_as_string!);
                        chart_values.push(d.doc_count!);
                    });

                    // Get our canvas and initiate the chart.
                    var ctx = document.getElementById("histogram");
                    scope.histogram = new Chart(ctx, {
                        type: scope.chartType,
                        data: {
                            labels: chart_labels,
                            datasets: [{
                                label: 'events',
                                data: chart_values,
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
