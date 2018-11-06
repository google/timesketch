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
import {tsButterbar} from './butterbar.directive';
import {tsEditSketch} from './edit-sketch.directive';
import {tsCoreUpload, tsCoreFileModel, tsCoreUploadQueue} from './upload.directive';

export const tsCoreModule = angular.module('timesketch.core', [])
  .directive('tsButterbar', tsButterbar)
  .directive('tsEditSketch', tsEditSketch)
  .directive('tsCoreUpload', tsCoreUpload)
  .directive('tsCoreFileModel', tsCoreFileModel)
  .directive('tsCoreUploadQueue', tsCoreUploadQueue);
