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

export const tsEventList = ['timesketchApi', function (timesketchApi) {
    /**
     * Render list of events (search result from the datastore).
     * @param sketch-id - The id for the sketch.
     * @param meta - Metadata object returned from the datastore search.
     * @param events - Array of events (search results).
     * @param query - Query string for the search results.
     * @param filter - Filter for the search results.
     * @param view-id - ID for the view.
     * @param named-view - Boolean indicating if the view is named.
     */
    return {
        restrict: 'E',
        template: require('./event-list.html'),
        scope: {
            sketchId: '=',
            sketch: '=',
            meta: '=',
            events: '=',
            query: '=',
            filter: '=',
            queryDsl: '=',
            viewId: '=',
            namedView: '=',
            similarityEnabled: '=',
            addEventData: '=',
        },
        require: '^tsSearch',
        controller: function ($scope) {
            // Convert to Javascript boolean
            $scope.similarityEnabled = ($scope.similarityEnabled == 'True')

            if ($scope.namedView) {
                timesketchApi.getView($scope.sketchId, $scope.viewId).success(function (data) {
                    $scope.view = data.objects[0]
                })
            }

            const toggleStar = function (event_list) {
                if (!event_list.length) {return}
                timesketchApi.saveEventAnnotation(
                    $scope.sketchId,
                    'label',
                    '__ts_star',
                    event_list).success(function (data) {})
            }

            const getSelectedEventsFilter = function () {
                const event_list: any[] = []
                const indices_list: any[] = []
                angular.forEach($scope.events, function (event) {
                    if (event.selected) {
                        indices_list.push(event['_index'])
                        event_list.push(
                            {
                                'doc_type': event['_type'],
                                'event_id': event['_id'],
                                'index': event['_index']})
                    }
                })
                return {'indices': indices_list, 'events': event_list}
            }

            $scope.toggleAll = function () {
                $scope.isAllSelected = $scope.events.every(function (event) {
                    return event.selected
                })
                angular.forEach($scope.events, function (event) {
                    if (!$scope.isAllSelected) {
                        event.selected = true
                    } else {
                        event.selected = false
                    }
                })
            }

            $scope.saveEventsView = function () {
                const filter = getSelectedEventsFilter()
                timesketchApi.saveView(
                    $scope.sketchId, $scope.view_name, false, '', filter, null)
                    .success(function (data) {
                        const view_id = data.objects[0].id
                        const view_url = '/sketch/' + $scope.sketchId + '/explore/view/' + view_id + '/'
                        window.location.href = view_url
                    },
                )
            }

            $scope.updateView = function () {
                let reload = false
                let query = ''
                let filter = getSelectedEventsFilter()
                let query_dsl = {}
                if (filter['events'].length < 1) {
                    query = $scope.query
                    filter = $scope.filter
                    query_dsl = $scope.queryDsl
                } else {
                    reload = true
                }
                timesketchApi.updateView(
                    $scope.sketchId, $scope.viewId, $scope.view.name, query, filter, query_dsl)
                    .success(function (data) {
                        if (reload) {
                            const view_id = data.objects[0].id
                            const view_url = '/sketch/' + $scope.sketchId + '/explore/view/' + view_id + '/'
                            window.location.href = view_url
                        }
                    })
            }

            $scope.deleteView = function () {
                timesketchApi.deleteView($scope.sketchId, $scope.viewId)
                    .success(function (data) {
                        const sketchUrl = '/sketch/' + $scope.sketchId + '/explore/'
                        window.location.href = sketchUrl
                    })
            }

            $scope.addStar = function () {
                const event_list: any[] = []
                angular.forEach($scope.events, function (event) {
                    if (event.selected && !event.star) {
                        event.star = true
                        event_list.push(event)
                    }
                })
                toggleStar(event_list)
            }

            $scope.removeStar = function () {
                const event_list: any[] = []
                angular.forEach($scope.events, function (event) {
                    if (event.selected && event.star) {
                        event.star = false
                        event_list.push(event)
                    }
                })
                toggleStar(event_list)
            }

            // ES limits our method of paging to the first 10k events.  Deep
            // pagination will require some major refactoring at a later date.
            // TODO(ajn): Correct this nonsense.
            $scope.getEventCount = function () {
                let event_count
                let total_pages
                if ($scope.meta.es_total_count > 10000) {
                    event_count = 10000
                    $scope.showLimitedResults = $scope.dataLoaded && true
                } else {
                    event_count = $scope.meta.es_total_count
                    $scope.showLimitedResults = $scope.dataLoaded && false
                }
                total_pages = Math.ceil(event_count / $scope.filter.size) - 1
                if (total_pages !== $scope.totalPages) {
                    $scope.currentPage = 0
                }
                $scope.totalPages = total_pages
            }

            $scope.buildPager = function () {
                const anchorLeft = 0
                const anchorRight = $scope.totalPages || 0
                const currentPage = $scope.currentPage || 0
                const pageRange = []
                for (let i = 0; i <= anchorRight; i++) {
                    if (i == 0 || i == anchorRight || i >= (currentPage - 2) && i < (currentPage + 3)) {
                        pageRange.push(i)
                    }
                }
                if ((currentPage - (anchorRight / 4)) > anchorLeft) {
                    const pageL = Math.floor(currentPage / 2)
                    if ( pageRange.indexOf( pageL ) === -1 ) {
                        pageRange.splice(1, 0, pageL)
                    }
                }
                if ((anchorRight - currentPage) > (anchorRight / 4)) {
                    const pageR = Math.floor((anchorRight - currentPage) / 2) + currentPage
                    if ( pageRange.indexOf( pageR ) === -1 ) {
                        pageRange.splice(-1, 0, pageR)
                    }
                }
                return pageRange
            }

            $scope.prevPage = function () {
                if ($scope.currentPage > 0) {
                    $scope.currentPage--;
                }
            }

            $scope.nextPage = function () {
                if ($scope.currentPage < $scope.totalPages - 1) {
                    $scope.currentPage++;
                }
            }

            $scope.setPage = function () {
                $scope.currentPage = this.n;
            }

            $scope.$watch('meta', function (value) {
                if (angular.isDefined(value)) {
                    if (angular.isDefined($scope.events)) {
                        $scope.dataLoaded = true
                        $scope.getEventCount()
                    }
                }
            })

            $scope.$watch('events', function (value) {
                if (angular.isDefined(value)) {
                    if (angular.isDefined($scope.meta) && $scope.meta.es_total_count > 0 && value.length ) {
                        $scope.dataLoaded = true
                        $scope.getEventCount()
                        $scope.buildPager()
                    }
                    $scope.anySelected = value.some(function (event) {
                        return event.selected
                    })
                }
            }, true)
        },

        link: function (scope, elem, attrs, ctrl) {
            scope.applyOrder = function () {
                ctrl.search(scope.query, scope.filter)
            }

            scope.$watch('pageSize', function (value) {
                scope.filter['size'] = scope.pageSize
                scope.currentPage = 0
                scope.dataLoaded = false
                ctrl.search(scope.query, scope.filter, scope.queryDsl)
            })

            scope.$watch('currentPage', function (value) {
                scope.filter['from'] = (scope.currentPage * scope.filter['size'])
                scope.dataLoaded = false
                ctrl.search(scope.query, scope.filter, scope.queryDsl)
            })
        },
    }
}]

export const tsEvent = function () {
    /**
     * Render event details.
     * @param sketch-id - The id for the sketch.
     * @param meta - Metadata object returned from the datastore search.
     * @param event - Event object.
     */
    return {
        restrict: 'E',
        template: require('./event.html'),
        scope: {
            sketchId: '=',
            meta: '=',
            event: '=',
            prevTimestamp: '=',
            nextTimestamp: '=',
            index: '=',
            isContextEvent: '=',
            enableContextQuery: '=',
            order: '=',
            similarityLayer: '=',
            addEventData: '=',
        },
        require: '?^tsSearch',
        controller: function ($scope, timesketchApi) {

            // Calculate the time delta in days between two events.
            const calcDays = function (t1, t2) {
                const t1_sec = Math.floor(t1 / 1000000)
                const t2_sec = Math.floor(t2 / 1000000)
                const delta = Math.floor(t1_sec - t2_sec)
                const delta_days = delta / 60 / 60 / 24
                return Math.floor(delta_days)
            }
            if ($scope.index > 0) {
                const event_timestamp = $scope.event['_source'].timestamp
                if ($scope.order == 'asc') {
                    $scope.days = calcDays(event_timestamp, $scope.prevTimestamp)
                } else {
                    $scope.days = calcDays(event_timestamp, $scope.nextTimestamp)
                }
            }

            // Get the color and name for the event here to prevent ugly template code.
            $scope.timeline_color = $scope.meta.timeline_colors[$scope.event._index]
            $scope.timeline_name = $scope.meta.timeline_names[$scope.event._index]

            // Defaults to not showing details for the event.
            $scope.showDetails = false

            if ('similarity_score' in $scope.event._source) {
                $scope.opacity = 1.0 - $scope.event._source.similarity_score
            } else {
                $scope.opacity = 1.0
            }

            $scope.toggleSelected = function () {
                $scope.event.selected = !$scope.event.selected
            }

            $scope.toggleStar = function () {
                timesketchApi.saveEventAnnotation(
                    $scope.sketchId,
                    'label',
                    '__ts_star',
                    $scope.event).success(function (data) {})
            }

            $scope.toggleHidden = function () {
                timesketchApi.saveEventAnnotation(
                    $scope.sketchId,
                    'label',
                    '__ts_hidden',
                    $scope.event).success(function (data) {
                    if ($scope.event.hidden) {
                        $scope.meta.numHiddenEvents++
                    } else {
                        $scope.meta.numHiddenEvents--
                    }
                })
            }

            $scope.addFilterStart = function () {
                $scope.$emit('datetime-clicked', {datetimeclicked: $scope.event._source.datetime})
            }

            // this function provides the hover effect/visual cues for manual
            // event addition.  we're not able to access the parent div from
            // a child via css, so we end up with this hacky thing.
            $scope.eventAddNgClass = ''
            $scope.eventAddHover = function (eventId) {
              if ($scope.addEventData[eventId].showForm) {
                  return
              }
              $scope.eventAddNgClass = 'event-insert-hover'
            }

            $scope.eventAddLeave = function ($event) {
              $scope.eventAddNgClass = ''
            }

            $scope.getDetail = function () {
                if ($scope.eventdetail) {return}
                timesketchApi.getEvent(
                    $scope.sketchId,
                    $scope.event._index,
                    $scope.event._id).success(function (data) {
                        $scope.eventdetail = data.objects
                        $scope.comments = data.meta.comments
                    })
            }

            $scope.postComment = function () {
                timesketchApi.saveEventAnnotation(
                    $scope.sketchId,
                    'comment',
                    $scope.formData.comment,
                    $scope.event).success(function (data) {
                        $scope.formData.comment = ''
                        $scope.commentForm.$setPristine()
                        $scope.comments.push(data['objects'][0][0])
                        $scope.comment = true
                    })
            }

            $scope.$watch('event', function (value) {
                $scope.star = false
                $scope.comment = false

                if ($scope.event._source.label.indexOf('__ts_star') > -1) {
                    $scope.event.star = true
                } else {
                    $scope.event.star = false
                }

                if ($scope.event._source.label.indexOf('__ts_comment') > -1) {
                    $scope.comment = true
                }

                if ($scope.event._source.label.indexOf('__ts_hidden') > -1) {
                    $scope.event.hidden = true
                    $scope.meta.numHiddenEvents++
                } else {
                    $scope.event.hidden = false
                }

            })
        },
        link: function (scope, elem, attrs, ctrl) {
            scope.getContext = function (event) {
                ctrl.getContext(event)
            }
        },
    }
}

export const tsEventAdd = ['$window', '$timeout', function ($window, $timeout) {
    /**
     * Render event details.
     * @param sketch-id - The id for the sketch.
     * @param meta - Metadata object returned from the datastore search.
     * @param event - Event object.
     */
    return {
        restrict: 'E',
        template: require('./event-add.html'),
        scope: {
            sketchId: '=',
            sketch: '=',
            event: '=',
            events: '=',
            filter: '=',
            query: '=',
            queryDsl: '=',
            index: '@',
            addEventData: '=',
        },
        require: '^tsSearch',
        controller: function ($scope, timesketchApi) {
            $scope.clearAddEvent = function (event) {
                $scope.addEventData[event._id].timestamp_desc = ''
                $scope.addEventData[event._id].message = ''
                $scope.addEventData[event._id].timestamp = event._source.datetime
                $scope.addEventData[event._id].showForm = !$scope.addEvent[event._id].showForm
            }
            $scope.genEventId = function () {
              let id = '';
              const alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_';
              for (let i = 0; i < 20; i++) {
                id += alpha.charAt(Math.floor(Math.random() * alpha.length));
              }
              return id;
            }
        },
        link: function (scope, elem, attrs, ctrl) {
            scope.doAddEvent = function (eventId, index) {
                const event = scope.addEventData[eventId]
                scope.addEventData[eventId].disabled = true
                ctrl.addEvent(event).then( function (response) {
                    const resp_timeline = response.data.objects[0]

                    if ( scope.filter.indices.indexOf( response.data.objects[0].searchindex.index_name ) == -1 ) {
                        scope.filter.indices.push( response.data.objects[0].searchindex.index_name )
                    }
                    let resp_timeline_active = false
                    for (const timeline of scope.sketch.active_timelines) {
                      if (timeline.searchindex.index_name == resp_timeline.searchindex.index_name) {
                        resp_timeline_active = true
                      }
                    }
                    if (!resp_timeline_active) {
                        scope.sketch.active_timelines.push(resp_timeline)
                    }

                    $timeout(function () {
                      ctrl.search(scope.query, scope.filter, scope.queryDsl)
                    }, 1000)
                })
            }
        },
    }
}]
