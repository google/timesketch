<!--
Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
    <!-- Progress indicator when loading sketch data -->
    <v-progress-linear v-if="loadingSketch" indeterminate color="primary"></v-progress-linear>

    <!-- Access Denied state -->
    <ts-sketch-access-denied v-if="sketchAccessDenied && !loadingSketch"></ts-sketch-access-denied>

    <div v-if="sketch.id && !loadingSketch && !sketchAccessDenied" style="height: 70vh">

      <!-- Empty state -->
      <v-container v-if="!hasTimelines && !loadingSketch && !isArchived && !sketchAccessDenied" class="fill-height" fluid>
        <v-row align="center" justify="center" class="text-center">
          <v-sheet class="pa-4" style="background: transparent">
              <v-img src="/assets/empty-state.png" max-height="100" max-width="300"></v-img>
              <div style="font-size: 2em" class="mb-3 mt-3">It's empty around here</div>
              <ts-upload-timeline-form-button btn-size="normal" btn-type="rounded"></ts-upload-timeline-form-button>
          </v-sheet>
        </v-row>
      </v-container>

      <!-- Archived state -->
      <v-container v-if="isArchived && !loadingSketch" fill-height fluid>
        <v-row align="center" justify="center">
          <v-sheet class="pa-4 text-center">
              <v-img src="/assets/empty-state.png" max-height="100" max-width="300"></v-img>
              <div style="font-size: 2em" class="mb-3 mt-3">This sketch is archived</div>
              <v-btn rounded depressed color="primary" @click="unArchiveSketch()"> Bring it back </v-btn>
          </v-sheet>
        </v-row>
      </v-container>

      <!-- Rename sketch dialog -->
      <v-dialog v-model="renameSketchDialog" width="600">
        <v-card class="pa-4">
          <ts-rename-sketch @close="renameSketchDialog = false"></ts-rename-sketch>
        </v-card>
      </v-dialog>

      <!-- Settings dialog -->
      <v-dialog v-model="showSettingsDialog" width="700px">
        <ts-settings-dialog></ts-settings-dialog>
      </v-dialog>

      <!-- Share dialog -->
      <v-dialog v-model="shareDialog" width="500">
          <ts-share-card @close-dialog="shareDialog = false"></ts-share-card>
      </v-dialog>

      <!-- Sketch AppBar -->
      <v-app-bar
        v-if="!loadingSketch"
        app
        clipped-left
        flat
        :color="theme.global.current.value.dark ? '#121212' : 'white'"
        :style="[
          theme.global.current.value.dark
            ? { 'border-bottom': '1px solid hsla(0,0%,100%,.12) !important' }
            : { 'border-bottom': '1px solid rgba(0,0,0,.12) !important' },
        ]"
      >
        <v-btn v-if="hasTimelines && !loadingSketch && !isArchived" icon @click.stop="toggleDrawer()">
          <v-icon title="Toggle left panel">mdi-menu</v-icon>
        </v-btn>

        <v-img
          src="/assets/timesketch-color.png"
          width="25"
          height="25"
          class="mt-1 flex-sm-0-0 mr-1 ml-1"
          style="cursor: pointer"
          @click="$router.push('/')"
        >
        </v-img>

        <v-hover v-slot="{ isHovering, props }">
          <div class="d-flex flex-wrap" v-bind="props">
            <div
              class="flex-1-0 ml-3"
              @dblclick="renameSketchDialog = true"
              style="
                font-size: 1.1em;
                cursor: pointer;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 900px;
              "
              :title="sketch.name"
            >
              {{ sketch.name }}
            </div>
            <div>
              <v-icon title="Rename sketch" size="small" v-if="isHovering" @click="renameSketchDialog = true"
                >mdi-pencil</v-icon
              >
            </div>
          </div>
        </v-hover>
        <v-spacer></v-spacer>

        <!-- Sharing dialog -->
        <v-btn size="small" variant="flat" rounded color="primary" class="mr-2" @click="shareDialog = !shareDialog">
          <v-icon small start>mdi-account-multiple-plus</v-icon>
          Share
        </v-btn>

        <v-avatar color="grey lighten-1" size="25" class="ml-3">
          <span class="white--text">{{ $filters.initialLetter(currentUser) }}</span>
        </v-avatar>

        <v-menu offset-y>
          <template v-slot:activator="{ props }">
              <v-btn size="small" icon v-bind="props" class="ml-2 mr-2">
                <v-icon title="Sketch Options">mdi-dots-vertical</v-icon>
              </v-btn>
          </template>
          <v-card>
            <v-list two-line>
              <v-list-item v-if="sketch.user">
                  <v-list-item-title>
                    <strong>Created:</strong> {{ $filters.shortDateTime(sketch.created_at) }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    <small>{{ $filters.shortDateTime(sketch.created_at) }} by {{ sketch.user.username }}</small>
                  </v-list-item-subtitle>
              </v-list-item>

              <v-list-item>
                  <v-list-item-title>
                    <strong>Access: </strong>
                    <span v-if="meta.permissions && meta.permissions.public">Public</span>
                    <span v-else>Restricted</span>
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    <small v-if="meta.permissions && meta.permissions.public"
                      >Visible to all users on this server</small
                    >
                    <small v-else>Only people with access can open</small>
                  </v-list-item-subtitle>
              </v-list-item>
            </v-list>

            <v-list>
                <v-list-item
                  v-on:click="toggleTheme"
                  prepend-icon="mdi-brightness-6"
                >
                  <v-list-item-title>Toggle theme</v-list-item-title>
                </v-list-item>

                <v-list-item
                  @click="renameSketchDialog = true"
                  prepend-icon="mdi-pencil"
                >
                  <v-list-item-title>Rename sketch</v-list-item-title>
                </v-list-item>

                <v-list-item
                  @click="archiveSketch()"
                  :disabled="isArchived"
                  prepend-icon="mdi-archive"
                >
                  <v-list-item-title>Archive sketch</v-list-item-title>
                </v-list-item>

                <v-list-item
                  v-if="meta.permissions && meta.permissions.delete"
                  @click="deleteSketch()"
                  prepend-icon="mdi-trash-can-outline"
                >
                  <v-list-item-title>Delete sketch</v-list-item-title>
                </v-list-item>

                <v-list-item
                  v-on:click="switchUI"
                  prepend-icon="mdi-view-dashboard-outline"
                >
                  <v-list-item-title>Use the old UI</v-list-item-title>
                </v-list-item>

                <v-list-item
                  @click="showSettingsDialog = true"
                  prepend-icon="mdi-cog-outline"
                >
                  <v-list-item-title>Settings</v-list-item-title>
                </v-list-item>

                <v-list-item
                  href="/logout/"
                  prepend-icon="mdi-logout"
                >
                  <v-list-item-title>Logout</v-list-item-title>
                </v-list-item>
            </v-list>
          </v-card>
        </v-menu>
      </v-app-bar>

      <!-- Left panel -->
      <v-navigation-drawer
        v-model="showLeftPanel"
        :disable-resize-watcher="true"
        :scrim="false"
        :width="navigationDrawer.width"
      >
      <!-- TODO: content of left panel -->
        <ts-investigation
          v-if="systemSettings.DFIQ_ENABLED || (systemSettings.LLM_FEATURES_AVAILABLE &&
            systemSettings.LLM_FEATURES_AVAILABLE.log_analyzer)"
          :icon-only="isMiniDrawer"
          @toggleDrawer="toggleDrawer()"
        >
        </ts-investigation>
        <!-- TODO: Replace with ts-search again once the explore/search view is feature complete in v3 -->
        <!-- <ts-search :icon-only="isMiniDrawer" @toggleDrawer="toggleDrawer()"></ts-search> -->
        <ts-v2-explore :icon-only="isMiniDrawer" @toggleDrawer="toggleDrawer()"></ts-v2-explore>
        <!-- <ts-tags :icon-only="isMiniDrawer" @toggleDrawer="toggleDrawer()"></ts-tags> -->
      </v-navigation-drawer>

      <!-- Main (canvas) view -->
      <router-view
        v-if="sketch.status && hasTimelines && !isArchived"
        @setTitle="(title) => (this.title = title)"
      ></router-view>

      <!-- Context search -->
      <v-bottom-sheet
        hide-overlay
        persistent
        no-click-animation
        v-model="showTimelineView"
        @click:outside="showTimelineView = false"
        scrollable
      >
        <v-card>
          <v-toolbar density="compact" color="transparent" class="px-3">
            <strong>Context search</strong>
            <v-btn-toggle v-model="contextTimeWindowSeconds" class="ml-10" density="compact" variant="outlined">
              <v-btn
                v-for="duration in [1, 5, 10, 60, 300, 600, 1800, 3600]"
                :key="duration"
                :value="duration"
                size="small"
                @click="updateContextQuery(duration)"
              >
              {{  $filters.formatSeconds(duration) }}
              </v-btn>
            </v-btn-toggle>
            <v-btn size="small" variant="text" class="ml-5" @click="contextToSearch()">Replace search</v-btn>

            <v-spacer></v-spacer>

            <v-btn icon :disabled="timelineViewHeight > 40" @click="increaseTimelineViewHeight()">
              <v-icon>mdi-chevron-up</v-icon>
            </v-btn>
            <v-btn icon :disabled="timelineViewHeight === 0" @click="decreaseTimelineViewHeight()">
              <v-icon>mdi-chevron-down</v-icon>
            </v-btn>
            <v-btn icon @click="showTimelineView = false">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-toolbar>
          <v-divider></v-divider>
          <v-expand-transition>
            <v-card-text :style="{ height: timelineViewHeight + 'vh' }" v-show="!minimizeTimelineView">
              <ts-event-list :query-request="queryRequest" :highlight-event="currentContextEvent"></ts-event-list>
            </v-card-text>
          </v-expand-transition>
        </v-card>
      </v-bottom-sheet>

    </div>
    <Notifications />
</template>

<script>
import ApiClient from '../utils/RestApiClient.js'
import dayjs from '@/plugins/dayjs'
import EventBus from '../event-bus.js'
import { useAppStore } from "@/stores/app";
import TsUploadTimelineFormButton from '../components/UploadFormButton.vue'
import { useTheme } from 'vuetify'
import TsRenameSketch from '../components/RenameSketch.vue'
import TsSettingsDialog from '../components/SettingsDialog.vue'
import TsShareCard from '../components/ShareCard.vue'
import TsSearch from '../components/LeftPanel/Search.vue'
import TsExampleLeftBar from '../components/LeftPanel/ExampleLeftBar.vue'
import TsEventList from '@/components/Explore/EventList.vue'
import TsInvestigation from '../components/LeftPanel/Investigation.vue'
import Notifications from '../components/Notifications.vue'
import TsV2Explore from '../components/LeftPanel/v2Explore.vue';
import TsSketchAccessDenied from '../components/SketchAccessDenied.vue';

export default {
  props: ['sketchId'],
  components: {
    TsRenameSketch,
    TsUploadTimelineFormButton,
    TsSettingsDialog,
    TsSearch,
    TsExampleLeftBar,
    TsShareCard,
    TsEventList,
    TsInvestigation,
    Notifications,
    TsV2Explore,
    TsSketchAccessDenied,
  },
  setup() {
    const theme = useTheme();
    return { theme };
  },
  data() {
    return {
      appStore: useAppStore(),
      showSketchMetadata: false,
      navigationDrawer: {
        width: 56,
      },
      isMiniDrawer: true,
      selectedScenario: null,
      scenarioDialog: false,
      showLeftPanel: false,
      leftPanelTab: 0,
      leftPanelTabItems: ['EXPLORE', 'INVESTIGATE'],
      renameSketchDialog: false,
      showHidden: false,
      shareDialog: false,
      loadingSketch: false,
      // Context
      timelineViewHeight: 60,
      showTimelineView: false,
      currentContextEvent: {},
      minimizeTimelineView: false,
      queryRequest: {},
      contextStartTime: null,
      contextEndTime: null,
      contextTimeWindowSeconds: 300,
      showFacetMenu: false,
      showQuestionMenu: false,
      showRightSidePanel: false,
      showSettingsDialog: false,
    }
  },
  mounted() {
    this.loadingSketch = true
    this.showLeftPanel = false
    this.appStore.updateSketch(this.sketchId).then(() => {
      this.appStore.updateSearchHistory(this.sketchId);
      this.appStore.updateScenarioTemplates(this.sketchId);
      this.appStore.updateSavedGraphs(this.sketchId);
      this.appStore.updateGraphPlugins();
      this.appStore.updateContextLinks();
      this.appStore.updateAnalyzerList(this.sketchId);
      this.appStore.updateSystemSettings();
      this.appStore.updateUserSettings().then(() => {
        if (this.userSettings.showLeftPanel) {
          this.toggleDrawer()
        }
      })
      if (this.hasTimelines && !this.isArchived) {
        this.showLeftPanel = true
      }
      this.updateDocumentTitle();
      this.loadingSketch = false
    })
    EventBus.$on('showContextWindow', this.showContextWindow)
  },
  beforeDestroy() {
    EventBus.$off('showContextWindow')
  },
  computed: {
    sketch() {
      return this.appStore.sketch
    },
    meta() {
      return this.appStore.meta
    },
    userSettings() {
      return this.appStore.settings
    },
    isArchived() {
      if (!this.sketch.status || !this.sketch.status.length) {
        return false
      }
      return this.sketch.status[0].status === 'archived'
    },
    currentUser() {
      return this.appStore.currentUser
    },
    hasTimelines() {
      return this.sketch.timelines && this.sketch.timelines.length
    },
    currentRouteName() {
      return this.$route.name
    },
    systemSettings() {
      return this.appStore.systemSettings
    },
    sketchAccessDenied() {
      return this.appStore.sketchAccessDenied
    },
  },
  methods: {
    archiveSketch: function () {
      this.loadingSketch = true
      ApiClient.archiveSketch(this.sketch.id)
        .then((response) => {
          this.appStore.updateSketch(this.sketch.id).then(() => {
            this.showLeftPanel = false
            this.loadingSketch = false
          })
        })
        .catch((e) => {
          console.error(e)
        })
    },
    unArchiveSketch: function () {
      this.loadingSketch = true
      ApiClient.unArchiveSketch(this.sketch.id)
        .then((response) => {
          this.appStore.updateSketch(this.sketch.id).then(() => {
            this.loadingSketch = false
            this.showLeftPanel = true
          })
        })
        .catch((e) => {
          console.error(e)
        })
    },
    deleteSketch: function () {
      if (confirm('Are you sure you want to delete the sketch?')) {
        ApiClient.deleteSketch(this.sketch.id)
          .then((response) => {
            this.$router.push({ name: 'Home' })
          })
          .catch((e) => {
            console.error(e)
          })
      }
    },
    generateContextQuery(event) {
      let timestampMillis = this.$filters.formatTimestamp(event._source.timestamp)
      this.contextStartTime = dayjs.utc(timestampMillis).subtract(this.contextTimeWindowSeconds, 'second')
      this.contextEndTime = dayjs.utc(timestampMillis).add(this.contextTimeWindowSeconds, 'second')
      let startChip = {
        field: '',
        value: this.contextStartTime.toISOString() + ',' + this.contextEndTime.toISOString(),
        type: 'datetime_range',
        operator: 'must',
        active: true,
      }
      let queryFilter = {
        from: 0,
        terminate_after: 40,
        size: 40,
        indices: ['_all'],
        order: 'asc',
        chips: [startChip],
      }
      let queryRequest = { queryString: '*', queryFilter: queryFilter }
      return queryRequest
    },
    updateContextQuery(duration) {
      this.contextTimeWindowSeconds = duration
      this.queryRequest = this.generateContextQuery(this.currentContextEvent)
    },
    contextToSearch() {
      let queryRequest = this.generateContextQuery(this.currentContextEvent)
      queryRequest.doSearch = true
      EventBus.$emit('setQueryAndFilter', queryRequest)
      this.showTimelineView = false
    },
    showContextWindow(event) {
      this.currentContextEvent = event
      this.queryRequest = this.generateContextQuery(event)
      this.showTimelineView = true
    },
    increaseTimelineViewHeight: function () {
      this.minimizeTimelineView = false
      if (this.timelineViewHeight > 70) {
        return
      }
      this.timelineViewHeight += 30
    },
    decreaseTimelineViewHeight: function () {
      this.minimizeTimelineView = false
      if (this.timelineViewHeight < 50) {
        this.minimizeTimelineView = true
        this.timelineViewHeight = 0
        return
      }
      this.timelineViewHeight -= 30
    },
    closeTimelineView: function () {
      this.minimizeTimelineView = true
      this.timelineViewHeight = 0
    },

    toggleTheme: function () {
      localStorage.setItem('isDarkTheme', this.theme.global.current.value.dark);
      this.theme.global.name.value = this.theme.global.current.value.dark ? 'light' : 'dark';
    },
    switchUI: function () {
      window.location.href = window.location.href.replace('/sketch/', '/legacy/sketch/')
    },
    toggleDrawer: function () {
      if (this.navigationDrawer.width > 56) {
        this.navigationDrawer.width = 56
        this.isMiniDrawer = true
      } else {
        this.navigationDrawer.width = 350
        setTimeout(() => {
          this.isMiniDrawer = false
        }, 100)
      }
    },
    updateDocumentTitle: function() {
      if (this.sketch && this.sketch.name && this.sketch.id) {
        document.title = `[${this.sketch.id}] ${this.sketch.name}`;
      } else {
        document.title = 'Timesketch';
      }
    },
  },
  watch: {
    sketch(newSketch) {
      if (newSketch) {
        this.updateDocumentTitle();
      }
    },
    hasTimelines(newVal, oldVal) {
      if (oldVal === 0 && newVal > 0) {
        this.showLeftPanel = true
      }
      if (oldVal > 0 && newVal === 0) {
        this.showLeftPanel = false
      }
    },
  },
}
</script>

