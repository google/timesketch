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
<template>
  <ts-timeline-component
    :timeline="timeline"
    :eventsCount="eventsCount"
    :isSelected="isSelected"
    :isEmptyState="isEmptyState"
    @toggle="$emit('toggle', ...arguments)"
    @disableAllOtherTimelines="$emit('disableAllOtherTimelines', ...arguments)"
    @save="$emit('save', ...arguments)"
    @remove="$emit('remove', ...arguments)"
  >
    <template v-slot:processing="slotProps">
      <v-chip v-on="slotProps.events.on" :style="timelineStyle(slotProps.timelineStatus)">
        <span class="timeline-name-ellipsis">{{ timeline.name }}</span>
        <span class="ml-1">
          <v-progress-circular small indeterminate color="grey" :size="20" :width="1"></v-progress-circular>
        </span>
      </v-chip>
    </template>
    <template v-slot:processed="slotProps">
      <v-chip
        @click="slotProps.events.toggleTimeline"
        :style="timelineStyle(slotProps.timelineStatus)"
        class="pr-1 timeline-chip"
        :class="[{ failed: slotProps.timelineFailed }, $vuetify.theme.dark ? 'dark-highlight' : 'light-highlight']"
        :ripple="!slotProps.timelineFailed"
      >
        <div class="chip-content">
          <v-icon v-if="slotProps.timelineFailed" title="Import failed; click for details" @click="slotProps.events.openDialog" left color="red" size="x-large">
            mdi-alert-circle-outline
          </v-icon>
          <v-icon v-if="!slotProps.timelineFailed" title="Toggle visibility" left :color="slotProps.timelineChipColor" size="26" class="ml-n2"> mdi-circle </v-icon>

          <v-tooltip bottom :disabled="timeline.name.length < 30" open-delay="200">
            <template v-slot:activator="{ on: onTooltip, attrs }">
              <span
                class="timeline-name-ellipsis"
                :class="{ disabled: !isSelected && (slotProps.timelineStatus === 'processing' || slotProps.timelineStatus === 'ready') }"
                v-bind="attrs"
                v-on="onTooltip"
                >{{ timeline.name }}</span
              >
            </template>
            <span>{{ timeline.name }}</span>
          </v-tooltip>

          <span class="right">
            <span v-if="slotProps.timelineStatus === 'processing'" class="ml-3">
              <v-progress-circular small indeterminate color="grey" :size="20" :width="2"></v-progress-circular>
            </span>

            <span v-if="!slotProps.timelineFailed" class="events-count" x-small>
              {{ eventsCount | compactNumber }}
            </span>
            <v-btn class="ma-1" x-small icon v-on="slotProps.events.menuOn">
              <v-icon title="Manage Timeline"> mdi-dots-vertical </v-icon>
            </v-btn>
          </span>
        </div>
      </v-chip>
    </template>
  </ts-timeline-component>
</template>

<script>

import TsTimelineComponent from '../Explore/TimelineComponent.vue'

export default {
  props: ['timeline', 'eventsCount', 'isSelected', 'isEmptyState'],
  components: {
    TsTimelineComponent,
  },
  methods: {
    timelineStyle(timelineStatus) {
      const greyOut = (timelineStatus === 'processing' || timelineStatus === 'ready') && !this.isSelected
      return {
        opacity: greyOut ? '50%' : '100%',
        backgroundColor: this.$vuetify.theme.dark ? '#303030' : '#f5f5f5',
      }
    },
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.timeline-chip {
  .right {
    margin-left: auto;
  }

  .chip-content {
    margin: 0;
    padding: 0;
    display: flex;
    align-items: center;
    width: 300px;
  }
}
.v-chip.timeline-chip.failed {
  cursor: auto;
}

.v-chip.timeline-chip.failed:hover:before {
  opacity: 0;
}

.events-count {
  font-size: 0.8em;
}

.disabled {
  text-decoration: line-through;
}

</style>

