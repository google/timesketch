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
export default {
  name: 'compactNumber',
  filter: function (input) {
    if (!input) {
      input = 0
    }
    let mark = ''
    if (input > 999999999) {
      input = Math.round((input / 1000000000) * 10) / 10
      mark = 'B'
    } else if (input > 999999) {
      input = Math.round((input / 1000000) * 10) / 10
      mark = 'M'
    } else if (input > 999) {
      input = Math.round((input / 1000) * 10) / 10
      mark = 'K'
    } else {
      return input
    }
    return input + mark
  }
}
