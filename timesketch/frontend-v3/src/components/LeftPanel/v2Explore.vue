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
  <div v-if="iconOnly" class="pa-4" style="cursor: pointer">
    <a :href="destinationUrl" style="color: inherit; text-decoration: none;">
      <v-icon left title="Search">mdi-magnify</v-icon>
      <div style="height: 1px"></div>
    </a>
  </div>

  <div v-else>
    <a :href="destinationUrl" style="text-decoration: none; color: inherit; display: block;">
        <div class="pa-4" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'" style="cursor: pointer">
            <v-icon left>mdi-magnify</v-icon>Search
        </div>
    </a>
    <v-divider></v-divider>
  </div>
</template>

<script>
import { useAppStore } from "@/stores/app";
import { useTheme } from 'vuetify';

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
  }
}
</script>

