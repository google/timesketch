/*
Copyright 2020 Google Inc. All rights reserved.

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
  name: 'compactBytes',
  filter: function (input) {
    // Based on https://gist.github.com/james2doyle/4aba55c22f084800c199
    if (!input) {
      input = 0
    }
    let units = ['B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    let exponent = Math.min(Math.floor(Math.log(input) / Math.log(1000)), units.length - 1)
    let num = (input / Math.pow(1000, exponent)).toFixed(2) * 1
    return num + units[exponent]
  }
}
