<!--
Copyright 2024 Google Inc. All rights reserved.

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
  <v-data-table
    :headers="headers"
    :items="allReadyTimelines"
    :search="search"
    :value="selectedTimelines"
    :dense="isDense"
    item-key="id"
    show-select
    @input="emitTimelineIDs"
  >
    <template v-slot:top>
      <v-text-field
        v-model="search"
        label="Filter timeline names"
        :dense="isDense"
      ></v-text-field>
    </template>
  </v-data-table>
</template>
  
<script>

export default {
  props: {
    selectedTimelineIDs: {
      type: Array,
      default: function() { return [] },
    },
    isDense: { type: Boolean, default: false },
  },
  data() {
    return {
      headers: [
        { value: 'name', text: 'Name'}, 
        { value: 'description', text: 'Description'},
        { value: 'id', text: 'ID'},
      ],
      search: '',
      timelineIDs: this.selectedTimelineIDs
    }
  },
  methods: {
    emitTimelineIDs(event) {
      let timelineIDs = event.map((t1) => t1.id)
      this.$emit('change', timelineIDs);
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    allReadyTimelines() {
      const timelines = this.sketch.timelines.filter(
        tl => tl.status[0].status === 'ready'
      );
      timelines.sort((a, b) => a.name.localeCompare(b.name))
      return timelines;
    },
    selectedTimelines() {
      let selected = this.allReadyTimelines.filter(
        (t1) => this.timelineIDs.includes(t1.id))
      return selected
    }
  },
  watch: {
    selectedTimelineIDs() {
      this.timelineIDs = this.selectedTimelineIDs
    }
  }
}
</script>

<style scoped lang="scss">
</style>