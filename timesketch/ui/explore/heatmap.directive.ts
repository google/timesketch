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
import * as d3 from 'd3'

export const tsHeatmap = function ($window, timesketchApi) {
    /**
     * Heatmap chart for number of events per hour/weekday.
     * @param sketchId - Sketch ID.
     * @param filter - Filter object.
     * @param query - Query string.
     * @param queryDsl - Query DSL JSON string.
     * @param meta - Events metadata object.
     * @param showCharts - Boolean indicating if chars should be visible.
     */
    return {
        restrict: 'E',
        scope: {
            sketchId: '=',
            filter: '=',
            query: '=',
            queryDsl: '=',
            meta: '=',
            showCharts: '=',
            disableChart: '=',
        },
        require: '^tsSearch',
        link: function (scope, element, attrs, ctrl) {
            scope.$watchGroup(['meta', 'showCharts'], function (newval, oldval) {
                if (scope.showCharts) {
                    timesketchApi.aggregation(scope.sketchId, scope.query, scope.filter, scope.queryDsl, 'heatmap')
                        .success(function (data) {
                            scope.render_heatmap(data['objects'])
                        })
                }
            }, true)

            // Handle window resize, and redraw the chart automatically.
            $window.onresize = function () {
                scope.$apply()
            }
            scope.$watch(function () {
                return angular.element($window)[0].innerWidth
            }, function () {
                if (scope.meta && scope.showCharts) {
                    timesketchApi.aggregation(scope.sketchId, scope.query, scope.filter, scope.queryDsl, 'heatmap')
                        .success(function (data) {
                            scope.render_heatmap(data['objects'])
                        })
                }
            })

            // Render the chart svg with D3.js
            scope.render_heatmap = function (data) {
                // Don't render chart if there is no data
                scope.disableChart = false
                if (data.length < 1) {
                  scope.disableChart = true
                  d3.select('svg').remove()
                  return
                }

                d3.select('svg').remove()
                const margin = { top: 50, right: 75, bottom: 0, left: 40 }
                const svgWidth = element[0].parentElement.parentElement.parentElement.offsetParent.offsetWidth - margin.left - margin.right
                const rectSize = Math.floor(svgWidth / 24)
                const svgHeight = Math.floor(rectSize * 9) - margin.top - margin.bottom
                const days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
                const hours = [
                  '00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
                  '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
                  '20', '21', '22', '23',
                ]

                const svg = d3.select(element[0]).append('svg')
                    .attr('width', svgWidth + margin.left + margin.right)
                    .attr('height', svgHeight + margin.top + margin.bottom)
                    .append('g')
                    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')

                const max_value_initial = d3.max(data, function (d) {
                    return d.count
                })
                let max_value = max_value_initial

                if (max_value_initial > 100000) {
                    max_value = max_value_initial / 100
                } else if (max_value_initial == 0) {
                    max_value = 1
                }

                // Generate color from color scale
                const genColor = d3.scaleLinear()
                    .domain([0, max_value / 2, max_value])
                    .range(['white', '#3498db', 'red'])

                const colors: any[] = []
                for (let i = 0; i < max_value; i++) {
                    colors.push(genColor(i))
                }
                const num_buckets = colors.length
                const colorScale = d3.scaleQuantile()
                    .domain([0, num_buckets - 1, max_value_initial])
                    .range(colors)

                svg.selectAll('.dayLabel')
                    .data(days)
                    .enter().append('text')
                    .text(function (d) {
                        return d
                    })
                    .attr('x', -12)
                    .attr('y', function (d, i) {
                        return i * rectSize
                    })
                    .style('text-anchor', 'end')
                    .attr('transform', 'translate(-6,' + rectSize / 1.5 + ')')

                svg.selectAll('.hourLabel')
                    .data(hours)
                    .enter().append('text')
                    .text(function (d) {
                        return d
                    })
                    .attr('x', function (d, i) {
                        return i * rectSize
                    })
                    .attr('y', -12)
                    .style('text-anchor', 'middle')
                    .attr('transform', 'translate(' + rectSize / 2 + ', -6)')

                // Create the heatmap
                const heatMap = svg.selectAll('.hour')
                    .data(data)
                    .enter().append('rect')
                    .attr('x', function (d) {
                        return (d.hour) * rectSize
                    })
                    .attr('y', function (d) {
                        return (d.day - 1) * rectSize
                    })
                    .attr('class', 'bordered')
                    .attr('width', rectSize)
                    .attr('height', rectSize)
                    .style('fill', 'white')

                // Fade in the chart and fill each box with color
                heatMap.transition().duration(500)
                    .style('fill', function (d) {
                        return colorScale(d.count)
                    })

                // Display event count on hover
                heatMap.append('title').text(function (d) {
                    return d.count
                })
            }
        },
    }
}
