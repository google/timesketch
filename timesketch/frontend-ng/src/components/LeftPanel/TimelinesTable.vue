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
  <div
    v-if="iconOnly"
    class="pa-4"
    style="cursor: pointer"
    @click="$emit('toggleDrawer'); expanded = true"
  >
    <v-icon start>mdi-clock-outline</v-icon>
    <div style="height: 1px"></div>
  </div>

  <div v-else>
    <div
      class="pa-4"
      style="cursor: pointer"
      @click="expanded = !expanded"
      :class="this.$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> <v-icon start>mdi-clock-outline</v-icon> Timelines </span>
      <ts-upload-timeline-form v-if="expanded">
        <template v-slot="slotProps">
          <v-btn
            v-bind="slotProps.attrs"
            v-if="expanded || allTimelines.length === 0"
            icon
            variant="text"
            class="float-right mt-n1 mr-n1"
            v-on="slotProps.on"
            @click.stop=""
          >
            <v-icon title="Add timeline">mdi-plus</v-icon>
          </v-btn>
        </template>
      </ts-upload-timeline-form>
      <span v-else class="float-right" style="margin-right: 10px">
        <small class="ml-3"
          ><strong>{{ allTimelines.length }}</strong></small
        >
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <v-text-field
          v-if="allTimelines.length >= paginationThreshold"
          class="ma-3"
          v-model="search"
          label="Filter timelines"
          single-line
          clearable
          hide-details
          variant="outlined"
          density="compact"
          prepend-inner-icon="mdi-magnify"
        ></v-text-field>
        <v-data-table
          class="data-table"
          :hide-default-footer="allTimelines.length <= paginationThreshold"
          :hide-default-header="true"
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
              class="mb-1 mt-1"
              :key="item.id + item.name"
              :is-selected="isEnabled(item)"
              @toggle="toggleTimeline"
              @disableAllOtherTimelines="disableAllOtherTimelines"
              :timeline="item"
            >
              <template v-slot:processing="slotProps">
                <div class="chip-content" :style="timelineStyle(slotProps.timelineStatus, isEnabled(item))">
                  <span class="timeline-name-ellipsis">{{ item.name }}</span>
                  <span class="float-right">
                    <span v-if="slotProps.timelineStatus === 'processing'" class="ml-3 mr-3">
                      <v-progress-circular small indeterminate color="grey" :size="17" :width="2"></v-progress-circular>
                    </span>
                  </span>
                </div>
              </template>
              <template v-slot:processed="slotProps">
                <div class="chip-content" :style="timelineStyle(slotProps.timelineStatus, isEnabled(item))">
                  <v-icon
                    v-if="slotProps.timelineFailed"
                    title="Import failed; click for details"
                    @click="slotProps.events.openDialog"
                    start
                    color="red"
                    size="x-large"
                    class="ml-n2"
                  >
                    mdi-alert-circle-outline
                  </v-icon>
                  <v-icon
                    v-if="!slotProps.timelineFailed"
                    start
                    :color="slotProps.timelineChipColor"
                    size="26"
                    class="ml-n2"
                  >
                    mdi-circle
                  </v-icon>

                  <v-tooltip location="bottom" :disabled="item.name.length < 40" open-delay="200">
                    <template v-slot:activator="{ props }">
                      <span v-bind="props" class="timeline-name-ellipsis" style="cursor: default">{{
                        item.name
                      }}</span>
                    </template>
                    <span>{{ item.name }}</span>
                  </v-tooltip>

                  <span class="float-right">
                    <span v-if="!slotProps.timelineFailed" class="events-count mr-1" x-small>
                      {{ this.$filters.compactNumber(getCount(item)) }}
                    </span>
                    <v-btn
                      v-if="!slotProps.timelineFailed"
                      class="ma-1"
                      size="x-small"
                      icon
                      @click="slotProps.events.toggleTimeline"
                    >
                      <v-icon v-if="isEnabled(item)"> mdi-eye </v-icon>
                      <v-icon v-else> mdi-eye-off </v-icon>
                    </v-btn>
                    <v-btn class="ma-1" size="x-small" icon v-on="slotProps.events.menuOn">
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
import EventBus from '../../event-bus.js'

import TsUploadTimelineForm from '../UploadForm.vue'
import TsTimelineComponent from '../Explore/TimelineComponent.vue'
export default {
  props: {
    iconOnly: Boolean,
  },
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
      const timelines = [...this.sketch.timelines]
      timelines.sort(function (a, b) {
        return a.name.localeCompare(b.name)
      })
      return timelines
    },
    activeTimelines() {
      // Sort alphabetically based on timeline name.
      const timelines = [...this.sketch.active_timelines]
      return timelines.sort(function (a, b) {
        return a.name.localeCompare(b.name)
      })
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
      headers: [{ value: 'name' }],
      paginationThreshold: 10,
    }
  },
  created() {
    this.$store.dispatch(
      'updateEnabledTimelines',
      this.activeTimelines.map((tl) => tl.id)
    )
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
  align-items: center;
  display: flex;
  margin-left: auto;
}
</style>
