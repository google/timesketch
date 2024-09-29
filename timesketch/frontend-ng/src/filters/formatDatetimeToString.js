/*
Copyright 2022 Google Inc. All rights reserved.

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
import dayjs from '@/plugins/dayjs'

export default {
  name: 'formatDatetimeToString',
  filter: function (datetime) {

    let timestamp = dayjs.utc(datetime)

    if (timestamp.unix() < 0) {
      return 'No timestamp'
    }
    else if (timestamp.isValid()) {
      return timestamp.format('YYYY-MM-DDTHH:mm:ss')
    }
    else {
      return 'No timestamp'
    }
  },
}
