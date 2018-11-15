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
import angular from 'angularjs-for-webpack';

export const tsEditSketch = function () {
    /**
     * Render Edit sketch modal.
     */
    return {
        restrict : 'E',
        scope: {},
        link : function (scope, element, attrs) {
            const modal_element = angular.element(document.getElementById('new-sketch-modal'));
            modal_element.modal('show');
        },
    };
};
