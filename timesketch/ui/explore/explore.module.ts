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
import {tsEvent, tsEventAdd, tsEventList} from './event.directive'
import {tsFilter, tsTimelinePickerItem} from './filter.directive'
import {tsHeatmap} from './heatmap.directive'
import {tsHistogram} from './histogram.directive'
import {tsJsonEditor} from './json-editor.directive'
import {
  tsSearch, tsSearchContextCard, tsSearchSavedViewPicker, tsSearchTemplatePicker,
} from './search.directive'

export const tsExploreModule = angular.module('timesketch.explore', [])
  .directive('tsEvent', tsEvent)
  .directive('tsEventAdd', tsEventAdd)
  .directive('tsEventList', tsEventList)
  .directive('tsFilter', tsFilter)
  .directive('tsTimelinePickerItem', tsTimelinePickerItem)
  .directive('tsHeatmap', tsHeatmap)
  .directive('tsHistogram', tsHistogram)
  .directive('tsJsonEditor', tsJsonEditor)
  .directive('tsSearch', tsSearch)
  .directive('tsSearchContextCard', tsSearchContextCard)
  .directive('tsSearchSavedViewPicker', tsSearchSavedViewPicker)
  .directive('tsSearchTemplatePicker', tsSearchTemplatePicker)
