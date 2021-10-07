<!--
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
-->
<template>
  <div>
    <ts-dropdown aria-role="list">
      <template v-slot:dropdown-trigger-element>
        <b-button style="width:215.5px;" :label="label" :icon-right="active ? 'chevron-up' : 'chevron-down'" />
      </template>
      <b-table :data="timelines" :columns="timelineColumns" :checked-rows.sync="selected" checkable> </b-table>
    </ts-dropdown>
  </div>
</template>

<script>
import TsDropdown from '../Common/Dropdown'

export default {
  props: [],
  components: { TsDropdown },
  data() {
    return {
      selected: [],
      timelineColumns: [
        {
          field: 'name',
        },
      ],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    timelines() {
      let timelines = []
      this.sketch.active_timelines.forEach(timeline => {
        let timelineId = timeline.id
        // Support for legacy timelines with 1:1 mapping to index_name
        let isLegacy = this.meta.indices_metadata[timeline.searchindex.index_name].is_legacy
        if (isLegacy) {
          timelineId = timeline.searchindex.index_name
        }
        timelines.push({
          id: timelineId,
          name: timeline.name,
        })
      })
      return timelines
    },
    label() {
      let label = 'Select individual timelines'
      if (this.selected.length) {
        label = 'Selected timelines (' + this.selected.length + '/' + this.timelines.length + ')'
      }
      return label
    },
  },
  watch: {
    selected(val) {
      this.$emit(
        'selectedTimelines',
        val.map(timeline => timeline.id)
      )
    },
  },
}
</script>
