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

export const tsSavedViewList = ['timesketchApi', function (timesketchApi) {
    /**
     * Render the list of saved views.
     */
    return {
        restrict: 'E',
        template: require('./views-list.html'),
        scope: {
            sketchId: '=',
            showSearchTemplates: '=',
            showDelete: '=',
        },
        controller: function ($scope) {
            timesketchApi.getViews($scope.sketchId).success(function (data) {
                $scope.savedViews = []
                const views = data.objects[0]
                if (views) {
                    for (const view of views) {
                        view.updated_at = moment.utc(view.updated_at).format('YYYY-MM-DD')
                        $scope.savedViews.push(view)
                    }
                }
            })

            $scope.deleteView = function (view) {
                timesketchApi.deleteView($scope.sketchId, view.id)
                const index = $scope.savedViews.indexOf(view)
                if (index > -1) {
                    $scope.savedViews.splice(index, 1)
                }
            }

            this.updateSavedViews = function (view) {
                $scope.savedViews.unshift(view)

            }
        },
    }
}]

export const tsSearchTemplateList = ['timesketchApi', function (timesketchApi) {
    /**
     * Render the list of search templates.
     */
    return {
        restrict: 'E',
        template: require('./search-template-list.html'),
        scope: {
            sketchId: '=',
        },
        require: '^tsSavedViewList',
        controller: function ($scope) {
            timesketchApi.getSearchTemplates().success(function (data) {
                $scope.searchTemplates = []
                const views = data.objects[0]
                if (views) {
                    for (const view of views) {
                        view.updated_at = moment.utc(view.updated_at).format('YYYY-MM-DD')
                        $scope.searchTemplates.push(view)
                    }
                }
            })

        },
        link: function (scope, elem, attrs, ctrl) {
            scope.addSearchTemplate = function (view) {
                timesketchApi.saveViewFromSearchTemplate(scope.sketchId, view.id).success(function (data) {
                    const view = data.objects[0]
                    view.updated_at = moment.utc(view.updated_at).format('YYYY-MM-DD')
                    ctrl.updateSavedViews(view)
                })
            }

        },
    }
}]
