<!--
Copyright 2025 Google Inc. All rights reserved.

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
  <div v-if="iconOnly" style="cursor: pointer">
    <a class="ai-navitem ai-navitem--closed" :href="destinationUrl" style="color: inherit; text-decoration: none">
      <div class="ai-navitem__icon">
        <v-icon left title="Search">mdi-magnify</v-icon>
      </div>
    </a>
  </div>

  <div v-else>
    <a :href="destinationUrl" style="text-decoration: none; color: inherit; display: block">
      <div :class="[$vuetify.theme.dark ? 'dark-hover' : 'light-hover', 'ai-navitem']" style="cursor: pointer">
        <div class="ai-navitem__icon"><v-icon left>mdi-magnify</v-icon></div>
        Search
      </div>
    </a>
  </div>
</template>

<script>
import { useAppStore } from '@/stores/app'
import { useTheme } from 'vuetify'

export default {
  data() {
    return {
      appStore: useAppStore(),
    }
  },
  props: {
    iconOnly: Boolean,
  },
  computed: {
    sketch() {
      return this.appStore.sketch
    },
    destinationUrl() {
      if (!this.sketch.id) {
        return '#'
      }
      return `/sketch/${this.sketch.id}/explore`
    },
  },
  setup() {
    return {
      theme: useTheme(),
    }
  },
}
</script>
