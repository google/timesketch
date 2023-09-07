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
    <v-btn small text color="primary" @click="selectAll()" class="mb-1">
      <v-icon left small>mdi-plus</v-icon>
      <span>Select all</span>
    </v-btn>
    <v-btn small text color="primary" @click="unselectAll()" class="mb-1">
      <v-icon left small>mdi-minus</v-icon>
      <span>Unselect all</span>
    </v-btn>
    <v-autocomplete
      v-model="selectedTimelines"
      :items="allTimelines"
      outlined
      label="Select timelines for analysis"
      item-text="name"
      item-value="id"
      multiple
      class="center-label-height"
    >
      <template v-slot:selection="data">
        <ts-timeline-chip
          :timeline="data.item"
          :close="true"
          @click:close="remove(data.item)"
        ></ts-timeline-chip>
      </template>
      <template v-slot:item="data">
        <v-list-item-content>
          <div>
              <ts-timeline-chip
                :timeline="data.item"
                :close="selectedTimelines.includes(data.item.id)"
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
  props: ['analyzerTimelineId'],
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
      const timelines = this.sketch.timelines.filter(
        tl => tl.status[0].status === 'ready'
      );
      timelines.sort((a, b) => a.name.localeCompare(b.name))
      return timelines;
    },
  },
  watch: {
    // add a watcher for selectedTimelines that emits the value to the parent
    selectedTimelines:  {
      handler: function (selection) {
        this.$emit('selectedTimelines', selection)
      },
      deep: true
    },
    analyzerTimelineId: {
      handler: function (id) {
        if (id) this.selectedTimelines.push(id)
        if (!id) this.selectedTimelines = []
      },
    },
  },
  methods: {
    remove (timeline) {
      this.selectedTimelines = this.selectedTimelines.filter(tl => tl!== timeline.id);
    },
    selectAll () {
      this.selectedTimelines = [...this.allTimelines.map(tl => tl.id)];
    },
    unselectAll () {
      this.selectedTimelines = [];
    },
  },

}
</script>

<style>
  /*
    Enforce a centered positioning of the append-icon. We can remove this once
    Vuetify provides a clean way of centering it.
  */
  .v-text-field--enclosed .v-input__append-inner {
    margin-top: auto !important;
    margin-bottom: auto !important;
  }
</style>
