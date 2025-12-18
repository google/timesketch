/*
Copyright 2025 Google Inc. All rights reserved.

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
  methods: {
    getTimeline(event) {
      let isLegacy = this.$store.state.meta.indices_metadata[event._index].is_legacy
      if (isLegacy) {
        return this.$store.state.sketch.active_timelines.find((timeline) => timeline.searchindex.index_name === event._index)
      }
      return this.$store.state.sketch.active_timelines.find((timeline) => timeline.id === event._source.__ts_timeline_id)
    },
  },
}
