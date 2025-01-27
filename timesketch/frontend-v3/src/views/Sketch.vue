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
  Sketch {{  this.appStore.sketch}}
</template>

<script>
import ApiClient from '../utils/RestApiClient.js'
import dayjs from '@/plugins/dayjs'
import EventBus from '../event-bus.js'
import { useAppStore } from "@/stores/app";

export default {
  props: ['sketchId'],
  components: {
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
      let timestampMillis = this.$options.filters.formatTimestamp(event._source.timestamp)
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
      this.$vuetify.theme.dark = !this.$vuetify.theme.dark
      localStorage.setItem('isDarkTheme', this.$vuetify.theme.dark.toString())
      let element = document.body
      element.dataset.theme = this.$vuetify.theme.dark ? 'dark' : 'light'
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

