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
      <v-toolbar dense flat>
        <v-avatar class="mt-2 ml-n4">
          <router-link to="/">
            <v-img src="/dist/timesketch-color.png" max-height="25" max-width="25" contain></v-img>
          </router-link>
        </v-avatar>
        <span style="font-size: 1.1em">{{ sketch.name }}</span>
      </v-toolbar>
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
