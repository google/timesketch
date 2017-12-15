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
import * as moment from 'moment'

export const tsTimelinesList = ['$interval', 'timesketchApi', function ($interval, timesketchApi) {
    /**
     * Render the list of timelines.
     */
    return {
        restrict: 'E',
        template: require('./timelines-list.html'),
        scope: {
            sketchId: '=',
            showEdit: '=',
            showDelete: '=',
        },
        controller: function ($scope) {
            // How often to poll the task API endpoint in milliseconds.
            const pollIntervall = 10000

            let getTimelines = function () {
                timesketchApi.getTimelines($scope.sketchId).success(function (data) {
                    $scope.timelines = []
                    let timelines = data.objects[0]
                    if (timelines) {
                        for (let timeline of timelines) {
                            console.log(timeline)
                            timeline.updated_at = moment.utc(timeline.updated_at).format('YYYY-MM-DD')
                            timeline.ready = true
                            let status = timeline.searchindex.status[0].status
                            if (status == 'processing') {
                                timeline.ready = false
                            }
                            $scope.timelines.push(timeline)
                        }
                    }
                })
            }

            $scope.deleteTimeline = function (timeline) {
                timesketchApi.deleteTimeline($scope.sketchId, timeline.id)
                const index = $scope.timelines.indexOf(timeline)
                if (index > -1) {
                    $scope.timelines.splice(index, 1)
                }
            }

            this.updateTimelines = function (timeline) {
                $scope.timelines.unshift(timeline)
            }

            getTimelines()
            $interval(function () {
                getTimelines()
            }, pollIntervall)

        },
    }
}]
