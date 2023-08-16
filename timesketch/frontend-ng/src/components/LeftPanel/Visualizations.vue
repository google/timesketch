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
    <div>
      <div
        :style="!(savedVisualizations && savedVisualizations.length) ? '' : 'cursor: pointer'"
        class="pa-4"
        @click="expanded = !expanded"
        :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
      >
        <span> <v-icon left>mdi-chart-bar</v-icon> Visualizations </span>
  
        <v-btn
          v-if="expanded || (savedVisualizations && savedVisualizations.length)"
          icon
          text
          class="float-right mt-n1 mr-n1"
          :to="{ name: 'NewVisualization', params: { sketchId: sketch.id } }"
          @click.stop=""
        >
          <v-icon>mdi-plus</v-icon>
        </v-btn>
        
      </div>
      <v-divider></v-divider>
    </div>
  </template>
  
  <script>
  
  export default {
    props: {
      startExpanded: Boolean,
    },
    components: {
    },
    data: function () {
      return {
      }
    },
    methods: {},
    computed: {
      savedVisualizations() {
        return this.$store.state.savedVisualizations
      },
      sketch() {
        return this.$store.state.sketch
      },
      meta() {
        return this.$store.state.meta
      },
    },
    mounted() {
    },
  }
  </script>
  
  <style scoped lang="scss">
  </style>
  