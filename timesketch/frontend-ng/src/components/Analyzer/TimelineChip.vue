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
  <v-chip class="timeline-chip" :style="getTimelineStyle()"
  @click:close="$emit('click:close')"
  :close="close"
  >
    <span class="timeline-name-ellipsis">{{ timeline.name }}</span>
  </v-chip>
</template>

<script>
export default {
  props: {
    timeline: Object,
    close: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  methods: {
    getTimelineStyle() {
      return {
        'background-color': this.normalizeBgColor(this.timeline.color),
      };
    },
    normalizeBgColor(bgColor) {
      return bgColor.startsWith('#') ? bgColor : `#${bgColor}`;
    }
  },
}
</script>

<style scoped lang="scss">
.timeline-chip {
  text-decoration: 'none';
  opacity: '100%';
}
.theme--dark.timeline-chip {
  filter: grayscale(25%);
  color: #333333;
}
.timeline-chip .theme--dark.v-icon{
  color: #333333;
}
</style>
