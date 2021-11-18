/*
Copyright 2019 Google Inc. All rights reserved.

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
import Vue from 'vue'

const requireFilter = require.context(
  // The relative path of the components folder
  '../filters',
  // Whether or not to look in subfolders
  false,
  // The regular expression used to match base component filenames
  /[A-Z]\w+\.(js)$/
)

requireFilter.keys().forEach(fileName => {
  // Get component config
  const filterModule = requireFilter(fileName)

  // Register filter globally
  Vue.filter(filterModule.default.name, filterModule.default.filter)
})
