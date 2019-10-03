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
  name: 'filterChip',
  filter: function (input) {
    if (input.operator === 'must') {
      return 'NOT ' + input.field + ':' + input.value
    } else if (input.field === 'ts_label') {
      if (input.value === '__ts_star') {
        return 'Starred'
      }
      return input.value
    } else if (input.operator === 'datetime_range') {
        let start = input.value.split(',')[0]
        let end = input.value.split(',')[1]
        return start + 'U+27f6' + end
    }
    return input.field + ':' + input.value
  }
}
