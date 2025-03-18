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
  <div
    v-if="iconOnly"
    class="pa-4"
    style="cursor: pointer"
    @click="$emit('toggleDrawer')"
  >
    <router-link
      :to="{ name: 'AiInvestigation', params: { sketchId: sketch.id } }"
    >
      <v-icon icon="mdi-creation" left />
      <div style="height: 1px"></div>
    </router-link>
  </div>

  <div v-else>
    <router-link
      :to="{ name: 'AiInvestigation', params: { sketchId: sketch.id } }"
      custom
      v-slot="{ navigate }"
      class="pa-4"
      :class="
        theme.global.current.value.dark
          ? isActive
            ? 'dark-highlight'
            : 'dark-hover'
          : isActive
          ? 'light-highlight'
          : 'light-hover'
      "
      style="cursor: pointer"
    >
      <div @click="navigate" @keypress.enter="navigate" role="link">
        <v-icon icon="mdi-creation" left />AI Investigation
      </div>
    </router-link>
    <v-divider></v-divider>
  </div>
</template>

<script>
import { useAppStore } from "@/stores/app";
import { useTheme } from "vuetify";
import { useRoute } from "vue-router";

export default {
  data() {
    return {
      appStore: useAppStore(),
      route: useRoute(),
    };
  },
  props: {
    iconOnly: Boolean,
  },
  computed: {
    sketch() {
      return this.appStore.sketch;
    },
    isActive() {
      return this.route.name === "AiInvestigation";
    },
    sketchId() {
      return this.appStore.sketch.id;
    },
  },
  setup() {
    return {
      theme: useTheme(),
    };
  },
};
</script>
