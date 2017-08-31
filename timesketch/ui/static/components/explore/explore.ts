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
import {tsEvent, tsEventList} from './explore-event-directive'
import {tsFilter, tsTimelinePickerItem} from './explore-filter-directive'
import {tsHeatmap} from './explore-heatmap-directive'
import {tsHistogram} from './explore-histogram-directive'
import {tsJsonEditor} from './explore-json-editor-directive'
import {
  tsSearch, tsSearchContextCard, tsSearchSavedViewPicker, tsSearchTemplatePicker
} from './explore-search-directive'

angular.module('timesketch.explore', [])
  .directive('tsEvent', tsEvent)
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
