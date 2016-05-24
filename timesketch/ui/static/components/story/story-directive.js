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

    module.directive('tsStory', function ($compile, $interval) {
        /**
         * Stories.
         */
        return {
            restrict: 'E',
            templateUrl: '/static/components/story/story.html',
            scope: {
                sketchId: '=',
                viewId: '='
            },
            link: function(scope, element, attrs, ctrl) {
                scope.sketch_id = attrs.sketchId;
                scope.view_id = attrs.viewId;
                scope.last_content = '';

                var set_content = function (content) {
                    scope.editor.setContent(content);
                    var new_editable = $('.editable');
                    var uncompiled_event_lists = new_editable.find('ts-story-event-list');
                    for (var i = 0; i < uncompiled_event_lists.length; i++) {
                        $compile($(uncompiled_event_lists[i]))(scope);
                    }
                };

                var save_draft = function() {
                    var editable = $('.editable').clone();

                    var event_lists = editable.find('ts-story-event-list');
                    for (var i = 0; i < event_lists.length; i++) {
                        $(event_lists[i]).empty();
                    }

                    var dropdowns = editable.find('ts-story-dropdown');
                    for (var i = 0; i < dropdowns.length; i++) {
                        $(dropdowns[i]).remove();
                    }
                    var serialized_content = editable[0].innerHTML.trim();
                    //  Only save if there are any changes to the document
                    if (serialized_content === scope.last_content) {
                        console.log("Nothing changed");
                        return
                    }
                    console.log(serialized_content);
                    scope.last_content = serialized_content;
                    //set_content(serialized_content);
                };

                $interval(function() {
                    save_draft();
                }, 10000);

                scope.titleEditor = new MediumEditor('.editable-title', {
                    placeholder: {
                        text: 'Title',
                        hideOnClick: false
                    },
                    disableReturn: true
                });

                scope.editor = new MediumEditor('.editable', {
                    placeholder: {
                        text: 'Your story starts here...',
                        hideOnClick: false
                    }
                });

                var editableEvents = ['editableKeyup', 'editableClick'];
                for (var i = 0; i < editableEvents.length; i++) {
                    scope.editor.subscribe(editableEvents[i], function (event, editable) {
                        var selection = window.getSelection();
                            range = selection.getRangeAt(0);
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
                            current.before(button)
                        }
                    });
                }
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
                    var query = data.objects[0].query_string;
                    var filter = angular.fromJson(data.objects[0].query_filter);
                    timesketchApi.search($scope.sketchId, query, filter).success(function(data) {
                        $scope.events = data.objects;
                        $scope.meta = data.meta;
                    });
                })
            }
        }
    }]);



})();
