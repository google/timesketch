<!--
Copyright 2019 Google Inc. All rights reserved.

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
    <!-- Left panel -->
    <v-navigation-drawer app permanent width="450" hide-overlay>
      <v-toolbar dense flat @click="showSketchMetadata = !showSketchMetadata" style="cursor: pointer">
        <v-avatar class="mt-2 ml-n4">
          <router-link to="/">
            <v-img src="/dist/timesketch-color.png" max-height="25" max-width="25" contain></v-img>
          </router-link>
        </v-avatar>
        <span style="font-size: 1.1em"
          >{{ sketch.name }}
          <v-icon class="ml-1" v-if="!showSketchMetadata">mdi-chevron-right</v-icon>
          <v-icon class="ml-1" v-else>mdi-chevron-down</v-icon>
        </span>
      </v-toolbar>
      <v-expand-transition>
        <v-list v-show="showSketchMetadata" two-line>
          <v-list-item>
            <v-list-item-content>
              <v-list-item-title> <strong>Created:</strong> {{ sketch.created_at | shortDateTime }} </v-list-item-title>
              <v-list-item-subtitle>
                <small>{{ sketch.created_at | timeSince }} by {{ sketch.user.username }}</small>
              </v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>

          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>
                <strong>Access: </strong>
                <span v-if="meta.permissions.public">Public</span>
                <span v-else>Restricted</span>
              </v-list-item-title>
              <v-list-item-subtitle>
                <small v-if="meta.permissions.public">Visibly to all users on this server</small>
                <small v-else>Only people with access can open</small>
              </v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>

          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>
                <strong>Shared with</strong>
              </v-list-item-title>
              <v-list-item-subtitle>
                <small>People and groups with access</small>
              </v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-expand-transition>
      <v-divider></v-divider>

      <ts-scenario :scenario="scenario"></ts-scenario>
      <br />
      <ts-saved-searches></ts-saved-searches>
      <ts-data-types></ts-data-types>
      <ts-tags></ts-tags>
    </v-navigation-drawer>

    <router-view v-if="sketch.status"></router-view>
  </div>
</template>

<script>
import TsScenario from '../components/Scenarios/Scenario'
import TsSavedSearches from '../components/LeftPanel/SavedSearches'
import TsDataTypes from '../components/LeftPanel/DataTypes'
import TsTags from '../components/LeftPanel/Tags'

export default {
  props: ['sketchId'],
  components: {
    TsScenario,
    TsSavedSearches,
    TsDataTypes,
    TsTags,
  },
  data() {
    return {
      showSketchMetadata: false,
    }
  },
  created: function () {
    this.$store.dispatch('updateSketch', this.sketchId)
    this.$store.dispatch('updateSearchHistory', this.sketchId)
    this.$store.dispatch('updateScenario', this.sketchId)
    this.$store.dispatch('updateSigmaList', this.sketchId)
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    scenario() {
      return this.$store.state.scenario
    },
  },
  watch: {
    sketch: function (newVal) {
      if (newVal.status[0].status === 'archived') {
        this.$router.push({ name: 'Overview', params: { sketchId: this.sketch.id } })
      }
      document.title = this.sketch.name
    },
  },
}
</script>
