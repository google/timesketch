
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
  <div class="content">
    <div class="pa-4"
         :style="'cursor: pointer'"
         @click="expanded = !expanded"
         :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
      <span> <v-icon left>mdi-timeline-clock-outline</v-icon> Timelines </span>
      <ts-upload-timeline-form v-if="expanded"
                               btn-type="small"></ts-upload-timeline-form>
      <span class="float-right"
            style="margin-right: 10px">
        <small class="ml-3"><strong>{{ allTimelines.length }}</strong></small>
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <v-text-field
          class="ma-3"
          v-model="search"
          append-icon="mdi-magnify"
          label="Filter timelines"
          single-line
          hide-details
        ></v-text-field>
        <v-data-table
        class="data-table"
          v-model="selected"
          :items="allTimelines"
          :headers="headers"
          item-key="id"
          dense
          disable-sort
          :search="search"
        >
          <template v-slot:item.name="{ item }">
            <ts-timeline-chip
              class="mb-1 mt-1 timeline-chip"
              :key="item.id + item.name"
              :is-selected="isEnabled(item)"
              @toggle="toggleTimeline"
              :timeline="item"
            ></ts-timeline-chip>
          </template>
        </v-data-table>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import TsUploadTimelineForm from '../UploadForm'
import TsTimelineChip from '../Explore/TimelineChip'
export default {
  props: [],
  components: {
    TsUploadTimelineForm,
    TsTimelineChip,
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    allTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.timelines]
      timelines.sort(function (a, b) {
        return a.name.localeCompare(b.name)
      })
      return timelines
    },

  },
  methods: {
    isEnabled(timeline) {
      return this.$store.state.enabledTimelines.includes(timeline.id)
    },
    toggleTimeline(timeline) {
      this.$store.dispatch('toggleEnabledTimeline', timeline.id)
    },
  },
  data: function () {
    return {
      expanded: false,
      selected: [],
      search: '',
      headers: [{ value: 'name' }]
    }
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.content::v-deep {

  .timeline-chip {
    display: inline-block;
  }
  .v-data-table__selected {
    background: none!important;
  }
  .v-data-table tbody tr:hover:not(.v-data-table__expanded__content) {
    background: none !important;
  }
  .v-data-table tbody tr:hover{
    background: none!important;
  }
  .v-data-table td{
    border-bottom: 0!important;
  }
  .v-data-table th{
    border-bottom: 0!important;
  }

  .v-data-footer {
    border-top: 0!important;
  }
}
</style>

