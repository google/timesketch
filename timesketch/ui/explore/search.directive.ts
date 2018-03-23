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

export const tsSearch = ['$location', 'timesketchApi', function ($location, timesketchApi) {
    /**
     * Search the datastore.
     * @param sketch-id - Sketch ID string.
     * @param view-id - Saved view ID string.
     * @param named-view - Boolean indicating if we are in view mode.
     */
    return {
        restrict: 'E',
        template: require('./search.html'),
        scope: {
            sketchId: '=',
            viewId: '=',
            namedView: '=',
            searchtemplateId: '=',
            similarityEnabled: '@',
        },
        controllerAs: 'ctrl',
        link: function (scope, elem, attrs, ctrl) {
            scope.$watch('sketch.views', function (value) {
                if (!scope.filter.indices.length) {
                    return
                }
                if (attrs.autoload == 'true') {
                    timesketchApi.getView(attrs.sketchId, attrs.viewId).success(function (data) {
                        const query = data.objects[0].query_string
                        const filter = angular.fromJson(data.objects[0].query_filter)
                        const queryDsl = angular.fromJson(data.objects[0].query_dsl)
                        if (queryDsl) {
                            scope.queryDsl = queryDsl
                            scope.showAdvanced = true
                        }

                        // Special case where all indices should be queried.
                        if (filter.indices == '_all') {
                            filter.indices = []
                            for (const timeline of scope.sketch.active_timelines) {
                                filter.indices.push(timeline.searchindex.index_name)
                            }
                        }
                        ctrl.search(query, filter, queryDsl)
                    })
                }
                if (attrs.redirect == 'true') {
                    scope.redirectView = true
                }
            }, true)
        },
        controller: function ($scope) {
            $scope.filter = {'indices': []}
            $scope.new_searchtemplate = false
            timesketchApi.getSketch($scope.sketchId).success(function (data) {
                $scope.sketch = data.objects[0]
                $scope.sketch.views = data.meta.views
                $scope.sketch.searchtemplates = data.meta.searchtemplates
                $scope.filter.indices = []
                for (const timeline of $scope.sketch.active_timelines) {
                    $scope.filter.indices.push(timeline.searchindex.index_name)
                }
            })

            $scope.$on('datetime-clicked', function (event, clickObj) {
                $scope.showFilters = true
                $scope.filter.time_start = clickObj.datetimeclicked
            })

            if ($scope.searchtemplateId) {
                timesketchApi.getSearchTemplate($scope.searchtemplateId).success(function (data) {
                    $scope.searchTemplate = data.objects[0]
                })
            }

            this.search = function (query, filter, queryDsl) {
                if (!filter.order) {
                    filter.order = 'asc'
                }

                if (filter.star && query) {
                    filter.star = false
                }

                if (filter.events && query || filter.star) {
                    delete filter.events
                }

                if (!filter.star && !filter.events && !query && !queryDsl) {
                    return
                }

                if (filter.time_start) {
                    $scope.showFilters = true
                }

                if (filter.context && query != '*') {
                    delete filter.context
                }

                $scope.events = []
                $scope.query = query
                $scope.filter = filter
                $scope.queryDsl = queryDsl

                timesketchApi.search($scope.sketchId, query, filter, queryDsl)
                    .success(function (data) {
                        $scope.events = data.objects
                        $scope.meta = data.meta
                        $scope.currentPage = 0
                        if (data.meta.es_total_count > filter['size']) {
                            $scope.meta.noisy = true
                        }
                        $scope.meta.numHiddenEvents = 0
                })
            }

            this.aggregation = function (query, filter, aggtype) {
                timesketchApi.aggregation($scope.sketchId, query, filter, aggtype)
                    .success(function (data) {
                        return data
                })
            }

            this.search_starred = function (query, filter) {
                filter.star = true
                query = ''
                filter.time_start = ''
                filter.time_end = ''
                this.search(query, filter)
            }

            this.saveView = function () {
                timesketchApi.saveView(
                    $scope.sketchId, $scope.view_name, $scope.new_searchtemplate, $scope.query, $scope.filter, $scope.queryDsl)
                    .success(function (data) {
                        $scope.new_searchtemplate = false
                        const view_id = data.objects[0].id
                        const view_url = '/sketch/' + $scope.sketchId + '/explore/view/' + view_id + '/'
                        window.location.href = view_url
                })
            }

            this.saveViewFromSearchTemplate = function (searchtemplateId) {
                timesketchApi.saveViewFromSearchTemplate($scope.sketchId, searchtemplateId).success(function (data) {
                    const view_id = data.objects[0].id
                    const view_url = '/sketch/' + $scope.sketchId + '/explore/view/' + view_id + '/'
                    window.location.href = view_url
                })
            }

            this.getContext = function (event) {
                const new_filter = {} as any
                const current_filter = $scope.filter
                const current_query = $scope.query
                const current_queryDsl = $scope.queryDsl
                angular.copy(current_filter, new_filter)

                const context_query = '*'

                if (!angular.isDefined(new_filter.context)) {
                    new_filter.context = {}
                    new_filter.context.query = current_query
                    new_filter.context.queryDsl = current_queryDsl
                    new_filter.context.sketchId = $scope.sketchId
                    new_filter.context.filter = current_filter
                    new_filter.context.seconds = 300
                    new_filter.context.event = {}
                    new_filter.context.meta = {}
                    angular.copy(event, new_filter.context.event)
                    angular.copy($scope.meta, new_filter.context.meta)
                }

                angular.copy(event, new_filter.context.event)
                new_filter.indices = [event._index]
                new_filter.time_start = moment(event._source.timestamp / 1000).utc().subtract(new_filter.context.seconds, 'seconds').format()
                new_filter.time_end = moment(event._source.timestamp / 1000).utc().add(new_filter.context.seconds, 'seconds').format()

                this.search(context_query, new_filter)
            }

            this.closeContext = function (context) {
                delete context.filter.context
                $scope.showFilters = false
                this.search(context.query, context.filter, context.queryDsl)
            }

            this.closeJSONEditor = function () {
                // Set the query string input to reflect the current DSL.
                try {
                    const currentQueryDsl = JSON.parse($scope.queryDsl)
                    $scope.query = currentQueryDsl['query']['filtered']['query']['query_string']['query']
                } catch (err) {}
                $scope.queryDsl = ''
                $scope.showAdvanced = false
            }
        },
    }
}]

export const tsSearchContextCard = function () {
    /**
     * Render the context card.
     */
    return {
        restrict: 'E',
        template: require('./search-context-card.html'),
        scope: {
            context: '=',
        },
        require: '^tsSearch',
        controllerAs: 'ctrl',
        link: function (scope, elem, attrs, ctrl) {
            scope.closeContext = function (context) {
                ctrl.closeContext(context)
            }
            scope.setInterval = function () {
                ctrl.getContext(scope.context.event)
            }
        },
    }
}

export const tsSearchSavedViewPicker = ['timesketchApi', function (timesketchApi) {
    /**
     * Render the list of saved views.
     */
    return {
        restrict: 'E',
        template: require('./search-saved-view-picker.html'),
        scope: false,
        require: '^tsSearch',
        link: function (scope, elem, attrs, ctrl) {
            scope.selectedView = {}
            scope.$watch('selectedView.view', function (value) {
                if (angular.isDefined(scope.selectedView.view)) {
                    if (angular.isDefined(scope.redirectView)) {
                        const view_url = '/sketch/' + scope.sketchId + '/explore/view/' + scope.selectedView.view.id + '/'
                        window.location.href = view_url
                    } else {
                        timesketchApi.getView(scope.sketchId, scope.selectedView.view.id).success(function (data) {
                            scope.query = data.objects[0].query_string
                            scope.filter = angular.fromJson(data.objects[0].query_filter)
                            scope.queryDsl = angular.fromJson(data.objects[0].query_dsl)
                            ctrl.search(scope.query, scope.filter, scope.queryDsl)
                        })
                    }
                }
            })
        },
    }
}]

export const tsSearchTemplatePicker = ['timesketchApi', function () {
    /**
     * Render the list of search templates.
     */
    return {
        restrict: 'E',
        template: require('./search-template-picker.html'),
        scope: false,
        require: '^tsSearch',
        link: function (scope, elem, attrs, ctrl) {
            scope.selectedTemplate = {}
            scope.$watch('selectedTemplate.template', function (value) {
                if (angular.isDefined(scope.selectedTemplate.template)) {
                    const template_url = '/sketch/' + scope.sketchId + '/explore/searchtemplate/' + scope.selectedTemplate.template.id + '/'
                    window.location.href = template_url
                }
            })
        },
    }
}]
