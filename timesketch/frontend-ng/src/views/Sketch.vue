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
  <div v-if="sketch" style="height: 30%">
    <v-progress-linear v-if="loadingSketch" indeterminate color="primary"></v-progress-linear>

    <!-- Top horizontal toolbar -->
    <v-toolbar flat color="transparent">
      <v-avatar v-show="!showLeftPanel || !hasTimelines" class="ml-n3 mt-1">
        <router-link to="/">
          <v-img src="/dist/timesketch-color.png" max-height="25" max-width="25" contain></v-img>
        </router-link>
      </v-avatar>
      <span v-show="!showLeftPanel && !loadingSketch" class="mr-1" style="font-size: 1.1em">{{ sketch.name }} </span>

      <v-btn icon v-show="!showLeftPanel && !loadingSketch" @click="toggleLeftPanel" class="ml-n1">
        <v-icon>mdi-menu</v-icon>
      </v-btn>

      <v-btn
        v-show="currentRouteName !== 'Explore'"
        :to="{ name: 'Explore', params: { sketchId: sketchId } }"
        color="primary"
        small
        text
        class="ml-3"
      >
        <v-icon small left>mdi-arrow-left</v-icon>
        back to explore
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn small depressed v-on:click="switchUI"> Use the old UI </v-btn>

      <!-- Sharing dialog -->
      <v-dialog v-model="shareDialog" width="500">
        <template v-slot:activator="{ on, attrs }">
          <v-btn small depressed color="primary" class="ml-2" v-bind="attrs" v-on="on">
            <v-icon small left>mdi-account-multiple-plus</v-icon>
            Share
          </v-btn>
        </template>
        <ts-share-card @close-dialog="shareDialog = false"></ts-share-card>
      </v-dialog>

      <v-avatar color="grey lighten-1" size="25" class="ml-3">
        <span class="white--text">{{ currentUser | initialLetter }}</span>
      </v-avatar>
      <v-menu offset-y>
        <template v-slot:activator="{ on, attrs }">
          <v-avatar>
            <v-btn small icon v-bind="attrs" v-on="on">
              <v-icon>mdi-dots-vertical</v-icon>
            </v-btn>
          </v-avatar>
        </template>
        <v-card>
          <v-list>
            <v-list-item-group color="primary">
              <v-list-item v-on:click="toggleTheme">
                <v-list-item-icon>
                  <v-icon>mdi-brightness-6</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Toggle theme</v-list-item-title>
                </v-list-item-content>
              </v-list-item>

              <v-list-item>
                <v-list-item-icon>
                  <v-icon>mdi-archive</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Archive sketch</v-list-item-title>
                </v-list-item-content>
              </v-list-item>

              <v-list-item>
                <v-list-item-icon>
                  <v-icon>mdi-export</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Export sketch</v-list-item-title>
                </v-list-item-content>
              </v-list-item>

              <a href="/logout/" style="text-decoration: none; color: inherit">
                <v-list-item>
                  <v-list-item-icon>
                    <v-icon>mdi-logout</v-icon>
                  </v-list-item-icon>

                  <v-list-item-content>
                    <v-list-item-title>Logout</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </a>
            </v-list-item-group>
          </v-list>
        </v-card>
      </v-menu>
    </v-toolbar>

    <!-- Empty state -->
    <v-container v-if="!hasTimelines && !loadingSketch" fill-height fluid>
      <v-row align="center" justify="center">
        <v-sheet class="pa-4">
          <center>
            <div style="font-size: 2em" class="mb-3">It's empty around here</div>
            <ts-upload-timeline-form btn-size="normal" btn-type="outlined"></ts-upload-timeline-form>
          </center>
        </v-sheet>
      </v-row>
    </v-container>

    <!-- Left panel -->
    <v-navigation-drawer
      v-if="showLeftPanel && hasTimelines"
      app
      permanent
      :width="navigationDrawer.width"
      hide-overlay
      ref="drawer"
    >
      <v-toolbar flat>
        <v-avatar class="ml-n3 mt-1">
          <router-link to="/">
            <v-img src="/dist/timesketch-color.png" max-height="25" max-width="25" contain></v-img>
          </router-link>
        </v-avatar>
        <div
          @click="showSketchMetadata = !showSketchMetadata"
          style="font-size: 1.1em; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis"
          :title="sketch.name"
        >
          {{ sketch.name }}
        </div>
        <v-spacer></v-spacer>
        <v-icon @click="toggleLeftPanel">mdi-chevron-left</v-icon>
      </v-toolbar>
      <v-expand-transition>
        <div class="px-4" v-show="showSketchMetadata">
          <v-dialog v-model="renameSketchDialog" width="600">
            <template v-slot:activator="{ on, attrs }">
              <v-btn small outlined depressed color="primary" v-bind="attrs" v-on="on">
                <v-icon left> mdi-pencil </v-icon>
                Rename</v-btn
              >
            </template>
            <v-card class="pa-4">
              <ts-rename-sketch @close="renameSketchDialog = false"></ts-rename-sketch>
            </v-card>
          </v-dialog>

          <v-list class="mx-n4" two-line>
            <v-list-item v-if="sketch.user">
              <v-list-item-content>
                <v-list-item-title>
                  <strong>Created:</strong> {{ sketch.created_at | shortDateTime }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  <small>{{ sketch.created_at | timeSince }} by {{ sketch.user.username }}</small>
                </v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>

            <v-list-item>
              <v-list-item-content>
                <v-list-item-title>
                  <strong>Access: </strong>
                  <span v-if="meta.permissions && meta.permissions.public">Public</span>
                  <span v-else>Restricted</span>
                </v-list-item-title>
                <v-list-item-subtitle>
                  <small v-if="meta.permissions && meta.permissions.public">Visible to all users on this server</small>
                  <small v-else>Only people with access can open</small>
                </v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>
        </div>
      </v-expand-transition>
      <v-divider></v-divider>

      <!-- Dialog for adding a scenario -->
      <v-dialog v-model="scenarioDialog" max-width="500px">
        <v-card>
          <div class="pa-3">
            <h3>Investigative Scenarios</h3>
            <v-select
              v-model="selectedScenario"
              :items="scenarioTemplates"
              item-text="display_name"
              return-object
              label="Select a scenario"
              outlined
              class="mt-3"
            ></v-select>
            <div v-if="selectedScenario">
              {{ selectedScenario.description }}
            </div>
          </div>
          <v-divider></v-divider>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn @click="scenarioDialog = false" color="primary" text> Close </v-btn>
            <v-btn :disabled="!selectedScenario" @click="addScenario(selectedScenario.short_name)" color="primary" text>
              Add
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <v-tabs v-model="leftPanelTab" grow>
        <v-tab v-for="item in leftPanelTabItems" :key="item"> {{ item }} </v-tab>
      </v-tabs>
      <v-divider></v-divider>
      <v-tabs-items v-model="leftPanelTab">
        <v-tab-item :transition="false">
          <ts-saved-searches v-if="meta.views"></ts-saved-searches>
          <ts-data-types></ts-data-types>
          <ts-tags></ts-tags>
          <ts-search-templates></ts-search-templates>
          <ts-sigma-rules></ts-sigma-rules>
          <ts-intelligence></ts-intelligence>
        </v-tab-item>
        <v-tab-item :transition="false">
          <ts-scenario v-for="scenario in activeScenarios" :key="scenario.id" :scenario="scenario"></ts-scenario>
          <v-row class="mt-0 px-2" flat>
            <v-col cols="6">
              <v-btn text color="primary" @click="scenarioDialog = true" style="cursor: pointer"
                ><v-icon left>mdi-plus</v-icon> Add Scenario</v-btn
              >
            </v-col>

            <v-col cols="6" align="right">
              <div v-if="hiddenScenarios.length" @click="showHidden = !showHidden" style="cursor: pointer" class="mt-1">
                <small
                  ><span v-if="showHidden">Hide</span><span v-else>Show</span> hidden scenarios ({{
                    hiddenScenarios.length
                  }})</small
                >
              </div>
            </v-col>
          </v-row>

          <div v-show="showHidden">
            <ts-scenario v-for="scenario in hiddenScenarios" :key="scenario.id" :scenario="scenario"></ts-scenario>
          </div>
        </v-tab-item>
      </v-tabs-items>
    </v-navigation-drawer>
    <router-view v-if="sketch.status && hasTimelines" @setTitle="(title) => (this.title = title)"></router-view>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

import TsScenario from '../components/Scenarios/Scenario'
import TsSavedSearches from '../components/LeftPanel/SavedSearches'
import TsDataTypes from '../components/LeftPanel/DataTypes'
import TsTags from '../components/LeftPanel/Tags'
import TsSearchTemplates from '../components/LeftPanel/SearchTemplates'
import TsSigmaRules from '../components/LeftPanel/SigmaRules'
import TsIntelligence from '../components/LeftPanel/ThreatIntel'
import TsUploadTimelineForm from '../components/UploadForm'
import TsShareCard from '../components/ShareCard'
import TsRenameSketch from '../components/RenameSketch'

export default {
  props: ['sketchId'],
  components: {
    TsScenario,
    TsSavedSearches,
    TsDataTypes,
    TsTags,
    TsSearchTemplates,
    TsSigmaRules,
    TsUploadTimelineForm,
    TsShareCard,
    TsRenameSketch,
    TsIntelligence,
  },
  data() {
    return {
      showSketchMetadata: false,
      navigationDrawer: {
        width: 370,
      },
      selectedScenario: null,
      scenarioDialog: false,
      showLeftPanel: false,
      leftPanelTab: 0,
      leftPanelTabItems: ['Explore', 'Investigate'],
      renameSketchDialog: false,
      showHidden: false,
      shareDialog: false,
      loadingSketch: false,
    }
  },
  mounted: function () {
    this.loadingSketch = true
    this.showLeftPanel = false
    this.$store.dispatch('updateSketch', this.sketchId).then(() => {
      this.$store.dispatch('updateSearchHistory', this.sketchId)
      this.$store.dispatch('updateScenarios', this.sketchId)
      this.$store.dispatch('updateScenarioTemplates', this.sketchId)
      this.$store.dispatch('updateContextLinks')
      this.loadingSketch = false
      this.showLeftPanel = true
      this.$nextTick(function () {
        this.setDrawerBorderStyle()
        this.setDrawerResizeEvents()
      })
    })
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    scenarios() {
      return this.$store.state.scenarios
    },
    scenarioTemplates() {
      return this.$store.state.scenarioTemplates
    },
    currentUser() {
      return this.$store.state.currentUser
    },
    activeScenarios() {
      if (!this.scenarios) {
        return []
      }
      return this.scenarios.filter((scenario) => !scenario.status.length || scenario.status[0].status === 'active')
    },
    hiddenScenarios() {
      if (!this.scenarios) {
        return []
      }
      return this.scenarios.filter((scenario) => scenario.status.length && scenario.status[0].status === 'hidden')
    },
    hasTimelines() {
      return this.sketch.timelines && this.sketch.timelines.length
    },
    currentRouteName() {
      return this.$route.name
    },
  },
  methods: {
    toggleTheme: function () {
      this.$vuetify.theme.dark = !this.$vuetify.theme.dark
      localStorage.setItem('isDarkTheme', this.$vuetify.theme.dark.toString())
    },
    switchUI: function () {
      window.location.href = window.location.href.replace('/v2/', '/')
    },
    addScenario: function (scenario) {
      this.scenarioDialog = false
      ApiClient.addScenario(this.sketch.id, scenario)
        .then((response) => {
          this.$store.dispatch('updateScenarios', this.sketch.id)
        })
        .catch((e) => {})
    },
    setDrawerBorderStyle() {
      let i = this.$refs.drawer.$el.querySelector('.v-navigation-drawer__border')
      i.style.cursor = 'ew-resize'
    },
    setDrawerResizeEvents() {
      const minSize = 1
      const drawerElement = this.$refs.drawer.$el
      const drawerBorder = drawerElement.querySelector('.v-navigation-drawer__border')
      const direction = drawerElement.classList.contains('v-navigation-drawer--right') ? 'right' : 'left'
      function resize(e) {
        document.body.style.cursor = 'ew-resize'
        let f = direction === 'right' ? document.body.scrollWidth - e.clientX : e.clientX
        drawerElement.style.width = f + 'px'
      }
      drawerBorder.addEventListener(
        'mousedown',
        (e) => {
          if (e.offsetX < minSize) {
            drawerElement.style.transition = 'initial'
            document.addEventListener('mousemove', resize, false)
          }
        },
        false
      )
      document.addEventListener(
        'mouseup',
        () => {
          drawerElement.style.transition = ''
          this.navigationDrawer.width = drawerElement.style.width
          document.body.style.cursor = ''
          document.removeEventListener('mousemove', resize, false)
        },
        false
      )
    },
    toggleLeftPanel() {
      this.showLeftPanel = !this.showLeftPanel
      if (this.showLeftPanel) {
        this.navigationDrawer.width = 370
      } else {
        this.navigationDrawer.width = 0
      }
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
