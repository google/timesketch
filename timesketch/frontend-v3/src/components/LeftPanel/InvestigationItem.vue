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
  <div v-if="iconOnly" style="cursor: pointer" @click="$emit('toggleDrawer')">
    <router-link
      class="ai-navitem ai-navitem--closed"
      :to="{ name: 'Investigation', params: { sketchId: sketch.id } }"
    >
      <div class="ai-navitem__icon">
        <v-icon v-if="menuTitle === 'Investigation'" icon="mdi-text-box-search-outline" />
        <CreationIcon v-else class="question-card__icon" :width="28" :height="28" />
      </div>
    </router-link>
  </div>

  <div v-else>
    <router-link
      :to="{ name: 'Investigation', params: { sketchId: sketch.id } }"
      custom
      v-slot="{ navigate }"
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
      <div @click="navigate" @keypress.enter="navigate" role="link" class="ai-navitem">
        <div class="ai-navitem__icon">
           <v-icon v-if="menuTitle === 'Investigation'" icon="mdi-text-box-search-outline" />
          <CreationIcon v-else class="question-card__icon" :width="28" :height="28" />
        </div>
        {{ menuTitle }}
      </div>
    </router-link>
  </div>
</template>

<script>
import CreationIcon from '@/components/Icons/CreationIcon'
import { useAppStore } from '@/stores/app'
import { useRoute } from 'vue-router'
import { useTheme } from 'vuetify'

export default {
  data() {
    return {
      appStore: useAppStore(),
      route: useRoute(),
    }
  },
  components: {
    CreationIcon,
  },
  props: {
    iconOnly: Boolean,
  },
  computed: {
    sketch() {
      return this.appStore.sketch
    },
    isActive() {
      return this.route.name === 'Investigation'
    },
    sketchId() {
      return this.appStore.sketch.id
    },
    meta() {
      return this.appStore.meta
    },
    systemSettings() {
      return this.appStore.systemSettings
    },
    menuTitle() {
      if (this.systemSettings.LLM_FEATURES_AVAILABLE?.log_analyzer) {
        return 'AI Investigation'
      } else if (this.systemSettings.DFIQ_ENABLED) {
        return 'Investigation'
      } else {
        return false
      }
    },
  },
  setup() {
    return {
      theme: useTheme(),
    }
  },
}
</script>
