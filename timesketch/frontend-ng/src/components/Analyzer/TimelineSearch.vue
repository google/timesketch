<!--
Copyright 2023 Google Inc. All rights reserved.

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
    <v-btn-toggle dense rounded class="mb-2">
      <v-btn small outlined rounded color="primary" @click="selectAll()">
        Select all
      </v-btn>
      <v-btn small outlined rounded color="primary" @click="unselectAll()">
        Unselect all
      </v-btn>
    </v-btn-toggle>
    <v-autocomplete
      v-model="selectedTimelines"
      :items="allTimelines"
      outlined
      dense
      chips
      label="Select timelines for analysis"
      item-text="name"
      item-value="name"
      multiple
      class="center-label-height"
    >
      <template v-slot:selection="data">
        <span class="my-2">
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
  </div>
</template>

<script>
import TsTimelineChip from '../Analyzer/TimelineChip'

export default {
  components:{
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
    selectAll () {
      this.selectedTimelines = [...this.allTimelines];
    },
    unselectAll () {
      this.selectedTimelines = [];
    },
  },

}
</script>

<style>
.center-label-height .v-input__prepend-inner, .center-label-height .v-input__append-inner {
  margin-top: 22px !important;
}
.center-label-height .v-label {
  margin-top: 7px !important;
}
</style>
