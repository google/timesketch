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
import * as $ from 'jquery'
import * as MediumEditor from 'medium-editor/dist/js/medium-editor.js'

export const tsStoryList = ['timesketchApi', function (timesketchApi) {
    /**
     * Render the list of stories.
     */
    return {
        restrict: 'E',
        template: require('./list.html'),
        scope: {
            sketchId: '=',
        },
        controller: function ($scope) {
            timesketchApi.getStories($scope.sketchId).success(function (data) {
                const stories = data.objects[0] || []
                $scope.stories = []
                for (const story of stories) {
                    story.created_at = moment.utc(story.created_at).format('YYYY-MM-DD HH:MM')
                    $scope.stories.push(story)
                }
            })
        },
    }
}]

export const tsCreateStory = ['timesketchApi', function (timesketchApi) {
    /**
     * Create story.
     */
    return {
        restrict: 'E',
        template: '<button class="btn btn-success" ng-click="createStory()"><i class="fa fa-plus"></i> Write a story</button>',
        scope: {
            sketchId: '=',
        },
        controller: function ($scope) {
            $scope.createStory = function () {
                timesketchApi.createStory($scope.sketchId).success(function (data) {
                    const storyId = data.objects[0].id
                    window.location.href = '/sketch/' + $scope.sketchId + '/stories/' + storyId + '/'
                })
            }
        },
    }
}]

export const tsStory = function (timesketchApi, $compile, $interval) {
    /**
     * Render a story.
     */
    return {
        restrict: 'E',
        template: require('./story.html'),
        scope: {
            sketchId: '=',
            storyId: '=',
        },

        link: function (scope, element, attrs, ctrl) {
            scope.sketch_id = attrs.sketchId
            scope.view_id = attrs.storyId
            scope.last_content = ''

            const set_content = function (title, content) {
                scope.titleEditor.setContent(title)
                scope.contentEditor.setContent(content)
                const new_editable = $('.editable')
                const uncompiled_event_lists = new_editable.find('ts-story-event-list')

                for (const uncompiled_event_list of uncompiled_event_lists) {
                    $compile($(uncompiled_event_list))(scope)
                }
            }

            const save_draft = function () {
                const editableTitle = $('.editable-title').clone()
                const editableContent = $('.editable').clone()

                // Empty the content of the event lists before saving
                angular.forEach(editableContent.find('ts-story-event-list'), function (element) {
                    $(element).empty()
                })

                // Remove all dropdown from the document before saving
                angular.forEach(editableContent.find('ts-story-dropdown'), function (element) {
                    $(element).remove()
                })

                // Current content of the doc
                const current_title = editableTitle[0].innerHTML.trim()
                const current_content = editableContent[0].innerHTML.trim()

                //  Only save if there are any changes to the document
                if (current_content === scope.last_content && current_title === scope.last_title) {
                    return
                }
                scope.last_content = current_content
                scope.last_title = current_title
                timesketchApi.updateStory(scope.sketchId, scope.storyId, current_title, current_content)
            }

            // Get the story on first load
            timesketchApi.getStory(scope.sketchId, scope.storyId).success(function (data) {
                const story = data.objects[0]
                const meta = data.meta
                story.updated_at = moment.utc(story.updated_at).format('YYYY-MM-DD HH:MM')
                scope.story = story
                scope.isEditable = meta['is_editable']

                // Setup the medium editors
                scope.titleEditor = new MediumEditor('.editable-title', {
                    placeholder: {
                        text: 'Title',
                        hideOnClick: false,
                    },
                    disableReturn: true,
                    toolbar: false,
                    disableEditing: !scope.isEditable,
                })

                scope.contentEditor = new MediumEditor('.editable', {
                    placeholder: {
                        text: 'Your story starts here...',
                        hideOnClick: false,
                    },
                    toolbar: scope.isEditable,
                    disableEditing: !scope.isEditable,
                })
                set_content(story.title, story.content)

                const editableEvents = ['editableKeyup', 'editableClick']
                for (const editableEvent of editableEvents) {
                    scope.contentEditor.subscribe(editableEvent, function (event, editable) {
                        const selection = window.getSelection()
                        const range = selection.getRangeAt(0)
                        const current = $(range.commonAncestorContainer)

                        // Remove button if the element is not the button itself
                        if (! current.closest('ts-story-dropdown').length) {
                            const buttons = $('.editable').find('ts-story-dropdown')
                            for (const button_elem of buttons) {
                                const button = $(button_elem)
                                button.remove()
                            }
                        }

                        if (current.length && current.text().trim() === '' && current.is('p')) {
                            const button = $compile('<ts-story-dropdown sketch-id="sketchId"></ts-story-dropdown>')(scope)
                            current.before(button)
                            save_draft()
                        }
                    })
                }
            })

            // Save document every 3 seconds if any change is detected
            $interval(function () {
                save_draft()
            }, 3000)
        },
    }
}

export const tsStoryDropdown = ['timesketchApi', '$compile', function (timesketchApi, $compile) {
    /**
     * Render the list of saved views for story.
     */
    return {
        restrict: 'E',
        template: require('./dropdown.html'),
        scope: {
            sketchId: '=',
        },
        controller: function ($scope) {
                    timesketchApi.getSketch($scope.sketchId).success(function (data) {
                        $scope.sketch = data.objects[0]
                        $scope.sketch.views = data.meta.views
                    })

        },
        link: function (scope, element, attrs, ctrl) {
            scope.selectedView = {}
            scope.$watch('selectedView.view', function (value) {
                if (angular.isDefined(scope.selectedView.view)) {
                    const el = (
                      '<ts-story-event-list contenteditable="false" sketch-id="'
                      + scope.sketchId + '" view-id="' + scope.selectedView.view.id
                      + '"></ts-story-event-list>'
                    )
                    const childNode = $compile(el)(scope)
                    element.hide()
                    element.after(childNode)
                    // Focus the next paragraph
                    const next_paragraph = $(childNode.next('p'))
                    const range = document.createRange()
                    const sel = window.getSelection()
                    range.setStart(next_paragraph[0], 0)
                    range.collapse(true)
                    sel.removeAllRanges()
                    sel.addRange(range)
                }
            })
        },
    }
}]

export const tsStoryEventList = ['timesketchApi', function (timesketchApi) {
    /**
     * Render the list of saved views for story.
     */
    return {
        restrict: 'E',
        template: require('./event-list.html'),
        scope: {
            sketchId: '=',
            viewId: '=',
        },
        controller: function ($scope) {
            timesketchApi.getView($scope.sketchId, $scope.viewId).success(function (data) {
                if (data.meta.deleted) {
                    $scope.deleted = true
                    $scope.viewName = data.meta.name
                }
                if (data.objects.length) {
                    const query = data.objects[0].query_string
                    const filter = angular.fromJson(data.objects[0].query_filter)
                    const queryDsl = angular.fromJson(data.objects[0].query_dsl)
                    $scope.viewName = data.objects[0].name
                    timesketchApi.search($scope.sketchId, query, filter, queryDsl).success(function (data) {
                        $scope.events = data.objects
                        $scope.meta = data.meta
                        $scope.filter = filter
                    })
                }
            })
        },
    }
}]
