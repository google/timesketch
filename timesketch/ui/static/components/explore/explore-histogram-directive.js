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
         * @param showCharts - Boolean indicating if chars should be visible.
         */
        return {
            restrict: 'E',
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

                // Handle window resize, and redraw the chart automatically.
                $window.onresize = function() {
                    scope.$apply();
                };
                scope.$watch(function() {
                    return angular.element($window)[0].innerWidth;
                }, function() {
                    if(scope.meta) {
                        timesketchApi.aggregation(scope.sketchId, scope.query, scope.filter, 'histogram')
                            .success(function(data) {
                                scope.render_histogram(data['objects'])
                            });
                    }
                });

                // Render the chart svg with D3.js
                scope.render_histogram = function(data) {
                    d3.select('.histogram').remove();

                    var margin = { top: 50, right: 75, bottom: 100, left: 40 },
                        svgWidth = d3.select(d3.select(element[0].parentElement.parentElement.parentElement.offsetParent.offsetWidth)) - margin.left - margin.right,
                        svgHeight = 500 - margin.top - margin.bottom;

                    var	parseDate = d3.time.format("%Y-%m-%d").parse;

                    var x = d3.scale.ordinal().rangeRoundBands([0, svgWidth], .05);
                    var y = d3.scale.linear().range([svgHeight, 0]);

                    var xAxis = d3.svg.axis()
                        .scale(x)
                        .orient("bottom")
                        .tickFormat(d3.time.format("%Y-%m-%d"));

                    var svg = d3.select(element[0]).append("svg")
                        .attr("width", svgWidth + margin.left + margin.right)
                        .attr("height", svgHeight + margin.top + margin.bottom)
                        .classed("histogram", true)
                        .append("g")
                        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

                    data.forEach(function(d) {
                        d.key_as_string = parseDate(d.key_as_string);
                        d.doc_count = +d.doc_count;
                    });

                    x.domain(data.map(function(d) { return d.key_as_string; }));
                    y.domain([0, d3.max(data, function(d) { return d.doc_count; })]);

                    svg.append("g")
                        .attr("class", "x axis")
                        .attr("transform", "translate(0," + svgHeight + ")")
                        .call(xAxis)
                        .selectAll("text")
                        .style("text-anchor", "end")
                        .attr("dx", "-.8em")
                        .attr("dy", "-.55em")
                        .attr("transform", "rotate(-90)" );

                    svg.selectAll("bar")
                        .data(data)
                        .enter().append("rect")
                        .style("fill", "steelblue")
                        .attr("x", function(d) { return x(d.key_as_string); })
                        .attr("width", x.rangeBand())
                        .attr("y", function(d) { return y(d.doc_count); })
                        .attr("height", function(d) { return svgHeight - y(d.doc_count); });
                };
            }
        }
    });
})();
