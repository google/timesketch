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
    <v-navigation-drawer app permanent :width="navigationDrawer.width" hide-overlay ref="drawer">
      <v-toolbar flat>
        <v-avatar class="mt-2 ml-n4">
          <router-link to="/">
            <v-img src="/dist/timesketch-color.png" max-height="25" max-width="25" contain></v-img>
          </router-link>
        </v-avatar>
        <span @click="showSketchMetadata = !showSketchMetadata" style="font-size: 1.1em; cursor: pointer"
          >{{ sketch.name }}
        </span>
        <v-spacer></v-spacer>
        <v-icon @click="hideDrawer()">mdi-chevron-left</v-icon>
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
  props: ['sketchId', 'showLeftPanel'],
  components: {
    TsScenario,
    TsSavedSearches,
    TsDataTypes,
    TsTags,
  },
  data() {
    return {
      showSketchMetadata: false,
      navigationDrawer: {
        width: 450,
      },
    }
  },
  created: function () {
    this.$store.dispatch('updateSketch', this.sketchId)
    this.$store.dispatch('updateSearchHistory', this.sketchId)
    this.$store.dispatch('updateScenario', this.sketchId)
    this.$store.dispatch('updateSigmaList', this.sketchId)
  },
  updated() {
    this.$nextTick(function () {
      this.setDrawerBorderStyle()
      this.setDrawerResizeEvents()
    })
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
  methods: {
    hideDrawer() {
      this.navigationDrawer.width = 0
      this.$emit('hideLeftPanel')
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
  },
  watch: {
    sketch: function (newVal) {
      if (newVal.status[0].status === 'archived') {
        this.$router.push({ name: 'Overview', params: { sketchId: this.sketch.id } })
      }
      document.title = this.sketch.name
    },
    showLeftPanel: function (newVal) {
      if (newVal === true) {
        this.navigationDrawer.width = 450
      }
    },
  },
}
</script>
