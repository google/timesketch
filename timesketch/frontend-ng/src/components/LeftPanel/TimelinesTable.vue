
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
            <ts-timeline-component
              class="mb-1 mt-1 "
              :key="item.id + item.name"
              :is-selected="isEnabled(item)"
              @toggle="toggleTimeline"
              @disableAllOtherTimelines="disableAllOtherTimelines"
              :timeline="item"
            >
            <template v-slot="slotProps">
              <div class="chip-content" :style="timelineStyle(slotProps.timelineStatus, isEnabled(item))">
                <v-icon v-if="slotProps.timelineFailed" @click="slotProps.events.openDialog" left color="red" size="x-large">
                  mdi-alert-circle-outline
                </v-icon>
                <v-icon v-if="!slotProps.timelineFailed" left :color="slotProps.timelineChipColor" size="26" class="ml-n2"> mdi-circle </v-icon>

                <v-tooltip bottom :disabled="item.name.length < 30" open-delay="300">
                  <template v-slot:activator="{ on: onTooltip, attrs }">
                    <span
                      class="timeline-name"
                      :class="{ disabled: !isEnabled(item) && slotProps.timelineStatus === 'ready' }"
                      v-bind="attrs"
                      v-on="onTooltip"
                      >{{ item.name }}</span
                    >
                  </template>
                  <span>test{{ item.name }}</span>
                </v-tooltip>

                <span class="right">
                  <span v-if="slotProps.timelineStatus === 'processing'" class="ml-3">
                    <v-progress-circular small indeterminate color="grey" :size="20" :width="2"></v-progress-circular>
                  </span>


                  <span v-if="!slotProps.timelineFailed" class="events-count" x-small>
                    {{ getCount(item) | compactNumber }}
                  </span>
                  <v-btn class="ma-1" x-small icon @click="slotProps.events.toggleTimeline">
                    <v-icon v-if="isEnabled(item)"> mdi-eye </v-icon>
                    <v-icon v-else> mdi-eye-off </v-icon>
                  </v-btn>
                  <v-btn class="ma-1" x-small icon v-on="slotProps.events.menuOn">
                    <v-icon> mdi-dots-vertical </v-icon>
                  </v-btn>
                </span>
              </div>
            </template>
          </ts-timeline-component>
          </template>
        </v-data-table>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import EventBus from '../../main'

import TsUploadTimelineForm from '../UploadForm'
import TsTimelineComponent from '../Explore/TimelineComponent'
export default {
  props: [],
  components: {
    TsUploadTimelineForm,
    TsTimelineComponent,
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
    disableAllOtherTimelines(timeline) {
      this.$store.dispatch('updateEnabledTimelines', [timeline.id])
    },
    timelineStyle(timelineStatus, isSelected) {
      const greyOut = timelineStatus === 'ready' && !isSelected
      return {
        opacity: greyOut ? '50%' : '100%',
      }
    },
    updateCountPerTimeline(countPerTimeline) {
      this.countPerTimeline = countPerTimeline
    },
    getCount(timeline) {
      let count = 0
      if (this.countPerTimeline) {
        count = this.countPerTimeline[timeline.id]
        if (typeof count === 'number') {
          return count
        }
      }
      return count
    },
  },
  data: function () {
    return {
      countPerTimeline: {},
      expanded: false,
      selected: [],
      search: '',
      headers: [{ value: 'name' }]
    }
  },
  mounted() {
    EventBus.$on('updateCountPerTimeline', this.updateCountPerTimeline)
  },
  beforeDestroy() {
    EventBus.$off('updateCountPerTimeline')
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
  .chip-content {
    flex: 1;
    margin: 0;
    padding: 0 10px;
    display: flex;
    align-items: center;
  }

  .timeline-name.disabled {
  text-decoration: line-through;

  }
  .right {
    margin-left: auto;
  }
</style>

