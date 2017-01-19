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
    var module = angular.module('timesketch.story.directive', []);

    module.directive('tsStoryList', ['timesketchApi', function(timesketchApi) {
        /**
         * Render the list of stories.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/story/story-list.html',
            scope: {
                sketchId: '=',
                showCreateButton: '='
            },
            controller: function($scope) {
                timesketchApi.getStories($scope.sketchId).success(function(data) {
                    var stories = data.objects[0];
                    $scope.stories = [];
                    for (var i = 0; i < stories.length; i++) {
                        var story = stories[i];
                        story.created_at = moment.utc(story.created_at).format("YYYY-MM-DD");
                        $scope.stories.push(story)
                    }
                });

                $scope.createStory = function () {
                    timesketchApi.createStory($scope.sketchId).success(function(data) {
                        var storyId = data.objects[0].id;
                        window.location.href = '/sketch/' + $scope.sketchId + '/stories/' + storyId + '/'
                    })
                }
            }
        }
    }]);

    module.directive('tsStory', function (timesketchApi, $compile, $interval) {
        /**
         * Render a story.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/story/story.html',
            scope: {
                sketchId: '=',
                storyId: '='
            },

            link: function(scope, element, attrs, ctrl) {
                scope.sketch_id = attrs.sketchId;
                scope.view_id = attrs.storyId;
                scope.last_content = '';

                var set_content = function (title, content) {
                    scope.titleEditor.setContent(title);
                    scope.contentEditor.setContent(content);
                    var new_editable = $('.editable'),
                        uncompiled_event_lists = new_editable.find('ts-story-event-list');

                    for (var i = 0; i < uncompiled_event_lists.length; i++) {
                        $compile($(uncompiled_event_lists[i]))(scope);
                    }
                };

                var save_draft = function() {
                    var editableTitle = $('.editable-title').clone(),
                        editableContent = $('.editable').clone();

                    // Empty the content of the event lists before saving
                    angular.forEach(editableContent.find('ts-story-event-list'), function(element) {
                        $(element).empty()
                    });

                    // Remove all dropdown from the document before saving
                    angular.forEach(editableContent.find('ts-story-dropdown'), function (element) {
                        $(element).remove()
                    });

                    // Current content of the doc
                    var current_title = editableTitle[0].innerHTML.trim(),
                        current_content = editableContent[0].innerHTML.trim();

                    //  Only save if there are any changes to the document
                    if (current_content === scope.last_content && current_title === scope.last_title) {
                        return
                    }
                    scope.last_content = current_content;
                    scope.last_title = current_title;
                    timesketchApi.updateStory(scope.sketchId, scope.storyId, current_title, current_content);
                };

                // Setup the medium editors
                scope.titleEditor = new MediumEditor('.editable-title', {
                    placeholder: {
                        text: 'Title',
                        hideOnClick: false
                    },
                    disableReturn: true,
                    toolbar: false

                });

                scope.contentEditor = new MediumEditor('.editable', {
                    placeholder: {
                        text: 'Your story starts here...',
                        hideOnClick: false
                    }
                });

                // Get the story on first load
                timesketchApi.getStory(scope.sketchId, scope.storyId).success(function (data) {
                    var story = data.objects[0];
                    set_content(story.title, story.content);
                });

                var editableEvents = ['editableKeyup', 'editableClick'];
                for (var i = 0; i < editableEvents.length; i++) {
                    scope.contentEditor.subscribe(editableEvents[i], function(event, editable) {
                        var selection = window.getSelection();
                            var range = selection.getRangeAt(0),
                                current = $(range.commonAncestorContainer);

                        // Remove button if the element is not the button itself
                        if (! current.closest('ts-story-dropdown').length) {
                            var buttons = $(".editable").find('ts-story-dropdown');
                            for (var i = 0; i < buttons.length; i++) {
                                var button = $(buttons[i]);
                                button.remove()
                            }
                        }

                        if (current.length && current.text().trim() === '' && current.is('p')) {
                            button = $compile('<ts-story-dropdown sketch-id="sketchId"></ts-story-dropdown>')(scope);
                            current.before(button);
                            save_draft()
                        }
                    });
                }

                // Save document every 3 seconds if any change is detected
                $interval(function() {
                    save_draft();
                }, 3000);
            }
        }
    });

    module.directive('tsStoryDropdown', ['timesketchApi', '$compile', function(timesketchApi, $compile) {
        /**
         * Render the list of saved views for story.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/story/story-dropdown.html',
            scope: {
                sketchId: '='
            },
            controller: function($scope) {
                        timesketchApi.getSketch($scope.sketchId).success(function(data) {
                            $scope.sketch = data.objects[0];
                            $scope.sketch.views = data.meta.views;
                        });

            },
            link: function(scope, element, attrs, ctrl) {
                scope.selectedView = {};
                scope.$watch('selectedView.view', function(value) {
                    if (angular.isDefined(scope.selectedView.view)) {
                        var el = '<ts-story-event-list contenteditable="false" sketch-id="'+ scope.sketchId + '" view-id="' + scope.selectedView.view.id + '"></ts-story-event-list>';
                        var childNode = $compile(el)(scope);
                        element.hide();
                        element.after(childNode);
                        // Focus the next paragraph
                        var next_paragraph = $(childNode.next('p'));
                        var range = document.createRange();
                        var sel = window.getSelection();
                        range.setStart(next_paragraph[0], 0);
                        range.collapse(true);
                        sel.removeAllRanges();
                        sel.addRange(range);
                    }
                })
            }
        }
    }]);

    module.directive('tsStoryEventList', ['timesketchApi', function(timesketchApi) {
        /**
         * Render the list of saved views for story.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/story/story-event-list.html',
            scope: {
                sketchId: '=',
                viewId: '='
            },
            controller: function($scope) {
                timesketchApi.getView($scope.sketchId, $scope.viewId).success(function(data) {
                    if (data.meta.deleted) {
                        $scope.deleted = true;
                        $scope.viewName = data.meta.name
                    }
                    if (data.objects.length) {
                        var query = data.objects[0].query_string;
                        var filter = angular.fromJson(data.objects[0].query_filter);
                        var queryDsl = angular.fromJson(data.objects[0].query_dsl);
                        $scope.viewName = data.objects[0].name;
                        timesketchApi.search($scope.sketchId, query, filter, queryDsl).success(function(data) {
                            $scope.events = data.objects;
                            $scope.meta = data.meta;
                            $scope.filter = filter;
                        });
                    }
                })
            }
        }
    }]);

})();
