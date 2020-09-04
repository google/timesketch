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
    if (input.operator === 'must_not') {
      return 'NOT ' + input.field + ':' + input.value
    } else if (input.type === 'label') {
      if (input.value === '__ts_star') {
        return 'Starred'
      } else if (input.value === '__ts_comment') {
        return 'Commented'
      }
      return input.value
    }
    return input.field + ':' + input.value
  }
}
