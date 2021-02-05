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
  <div class="tag is-medium has-text-left" style="background-color: #f5f5f5; padding-left: 5px;">
    <div style="width: 20px; height: 20px; border-radius: 6px; margin-right: 10px;" v-bind:style="timelineColorStyle"></div>
    <div style="font-weight: normal;">{{ timeline.name }}</div>
  </div>
</template>

<script>

export default {
  props: ['timeline'],
  computed: {
    timelineColorStyle () {
      let backgroundColor = this.timeline.color
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
      }
      return {
        'background-color': backgroundColor
      }
    }
  }
}
</script>
