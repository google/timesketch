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
  <ts-timeline-component
    :timeline="timeline"
  >
    <template v-slot:processed="slotProps">
      <v-chip
        :style="timelineStyle"
        class="timeline-chip"
        :ripple="false"
        :closable="close"
        @click:close="$emit('click:close')"
      >
        <div class="chip-content">
          <v-icon start :color="slotProps.timelineChipColor" size="26" class="ml-n2"> mdi-circle </v-icon>
          <v-tooltip location="bottom" :disabled="timeline.name.length < 30" open-delay="200">
            <template v-slot:activator="{ props }">
              <span
                class="timeline-name-ellipsis"
               
                v-bind="props"
                >{{ timeline.name }}</span
              >
            </template>
            <span>{{ timeline.name }}</span>
          </v-tooltip>
        </div>
      </v-chip>
    </template>
  </ts-timeline-component>
</template>

<script>
import TsTimelineComponent from '../Explore/TimelineComponent.vue'

export default {
  props: {
    timeline: Object,
    close: {
      type: Boolean,
      default: false
    }
  },
  components: {
    TsTimelineComponent,
  },
  computed: {
    timelineStyle() {
      return {
        backgroundColor: this.$vuetify.theme.dark ? '#4d4d4d' : '#e6e6e6',
      }
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.timeline-chip {
  .chip-content {
    margin: 0;
    padding: 0;
    display: flex;
    align-items: center;
    width: 300px;
  }

  .timeline-name-ellipsis {
    width: 300px;
  }
}
</style>
