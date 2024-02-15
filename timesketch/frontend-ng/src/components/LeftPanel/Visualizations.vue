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
    key="iconOnly"
    class="pa-4"
    style="cursor: pointer"
    @click="
      $emit('toggleDrawer')
      expanded = true
    "
  >
    <v-icon left>
      mdi-chart-bar
    </v-icon>
    <div style="height: 1px">
    </div>
  </div>
  <div 
    v-else
    key="iconOnly"
  >
    <div
      :style="!(savedVisualizations && savedVisualizations.length) ? '' : 'cursor: pointer'"
      class="pa-4"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> 
        <v-icon left>
          mdi-chart-bar
        </v-icon> 
        Visualizations 
      </span>
  
      <v-btn
        icon
        text
        class="float-right mt-n1 mr-n1"
        :to="{ name: 'VisualizationNew' }"
        @click.stop=""
      >
        <v-icon title="Create a new visualization">
          mdi-plus
        </v-icon>
      </v-btn>
      <span 
        v-if="!expanded" 
        class="float-right" 
        style="margin-right: 10px"
      >
        <small 
          v-if="savedVisualizations && savedVisualizations.length"
        >
          <strong>
            {{ visualizationCount }}
          </strong>
        </small>
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded && savedVisualizations.length">
        <router-link
          v-for="(savedVisualization, key) in savedVisualizations"
          :key="key"
          :to="{ 
            name: 'VisualizationView', 
            params: { aggregationId: savedVisualization.id } 
          }"
          style="cursor: pointer; font-size: 0.9em; text-decoration: none"
          
        >
          <v-row no-gutters class="pa-2 pl-5" 
          :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
          <span :class="$vuetify.theme.dark ? 'dark-font' : 'light-font'">
              {{ savedVisualization.name }}
            </span>
        </v-row>
        </router-link>
        <!-- <v-list 
          v-if="savedVisualizations && savedVisualizations.length"
        >
          <v-list-item 
            v-for="(savedVisualization, key) in savedVisualizations"
            :key="key"
            :to="{ 
              name: 'VisualizationView', 
              params: { aggregationId: savedVisualization.id } 
            }"
            style="cursor: pointer; font-size: 0.9em; text-decoration: none"
            class="pa-2 pl-5" 
            :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
          >
            <span :class="$vuetify.theme.dark ? 'dark-font' : 'light-font'">
              {{ savedVisualization.name }}
            </span>
          </v-list-item>
        </v-list> -->
      </div>
    </v-expand-transition>
  </div>
</template>
  
<script>

export default {
  props: {
    iconOnly: {
      type: Boolean,
    },
  },
  data: function () {
    return {
      expanded: false,
    }
  },
  methods: {},
  computed: {
    savedVisualizations() {
      return this.$store.state.savedVisualizations
    },
    visualizationCount() {
      if (!this.$store.state.savedVisualizations) {
        return 0
      }
      return this.$store.state.savedVisualizations.length
    }, 
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  mounted() {
    this.$store.dispatch('updateSavedVisualizationList', this.sketch.id)
  },
}
</script>
