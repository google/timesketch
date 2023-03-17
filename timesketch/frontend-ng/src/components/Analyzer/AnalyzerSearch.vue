<!--
Copyright 2021 Google Inc. All rights reserved.

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

<script>
import TsSearchDropdown from '../Explore/SearchDropdown'
import TsTimelineChip from '../Analyzer/TimelineChip'

export default {
  components:{
    TsSearchDropdown,
    TsTimelineChip,
  },
  data() {
    return {
      selectedTimelines: [],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    allTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.timelines]
      timelines.sort((a, b) => a.name.localeCompare(b.name))
      return timelines;
    },

  },
  methods: {
    remove (timeline) {
      this.selectedTimelines = this.selectedTimelines.filter(tl => tl!== timeline.name);
    },
  },

}
</script>

<template>
  <v-autocomplete
    v-model="selectedTimelines"
    :items="allTimelines"
    outlined
    dense
    chips
    label="Timelines"
    item-text="name"
    item-value="name"
    multiple
  >
    <template v-slot:selection="data">
      <span class="chip">
        <ts-timeline-chip
          :timeline="data.item"
          :close="true"
          @click:close="remove(data.item)"
        ></ts-timeline-chip>
      </span>
    </template>
    <template v-slot:item="data">
      <v-list-item-content>
        <div>
            <ts-timeline-chip
              :timeline="data.item"
              :close="selectedTimelines.includes(data.item.name)"
              @click:close="remove(data.item)"
            ></ts-timeline-chip>
        </div>
      </v-list-item-content>
    </template>
  </v-autocomplete>

</template>

<style scoped lang="scss">
.chip {
  margin: 10px 5px;
  margin-left: 0;
}

</style>
