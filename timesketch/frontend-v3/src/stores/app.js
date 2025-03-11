/*
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
*/

import ApiClient from '../utils/RestApiClient.js'
import { defineStore } from "pinia";

export const useAppStore = defineStore("app", {
  state: () => ({
    sketch: {},
    meta: {},
    searchHistory: {},
    scenarios: [],
    hiddenScenarios: [],
    scenarioTemplates: [],
    graphPlugins: [],
    savedGraphs: [],
    tags: [],
    dataTypes: [],
    count: 0,
    currentSearchNode: null,
    currentUser: undefined,
    settings: {},
    systemSettings: {},
    activeContext: {
      scenario: {},
      facet: {},
      question: {},
    },
    snackbar: {
      active: false,
      color: '',
      message: '',
      timeout: -1,
    },
    contextLinkConf: {},
    sketchAnalyzerList: {},
    savedVisualizations: [],
    activeAnalyses: [],
    analyzerResults: [],
    enabledTimelines: [],
  }),
  actions: {
    async setTestAppStore() {
      this.testAppStore = "🚀 Pinia state storage is operational!";
    },

    resetState() {
      ApiClient.getLoggedInUser().then((response) => {
        let currentUser = response.data.objects[0].username;
        this.$reset();
        this.currentUser = currentUser;
      })
    },

    async updateSketch(sketchId) {
      try {
        const response = await ApiClient.getSketch(sketchId);
          this.sketch = response.data.objects[0];
          this.meta = response.data.meta;
        const userResp = await ApiClient.getLoggedInUser();
        let currentUser = userResp.data.objects[0].username;
        this.currentUser = currentUser;
        await this.updateTimelineTags(sketchId);
        await this.updateDataTypes(sketchId);
      } catch (e) {
      }
    },

    async updateTimelineTags(sketchId) {
      if (!this.sketch.active_timelines.length) {
        return
      }
      let formData = {
        aggregator_name: 'field_bucket',
        aggregator_parameters: {
          field: 'tag',
          limit: '1000',
        },
      }
      try {
        const response = await ApiClient.runAggregator(sketchId, formData);
        this.tags = response.data.objects[0]['field_bucket']['buckets'];
      } catch (e) {
      }
    },

    async updateDataTypes(context, sketchId) {
      if (!this.sketch.active_timelines.length) {
        return
      }
      let formData = {
        aggregator_name: 'field_bucket',
        aggregator_parameters: {
          field: 'data_type',
          limit: '1000',
        },
      }

      try {
        const response = await ApiClient.runAggregator(sketchId, formData);
        this.dataTypes = response.data.objects[0]['field_bucket']['buckets']
      } catch (e) {
      }
    },

    async updateSearchHistory(sketchId) {
      if (!sketchId) {
        sketchId = this.sketch.id;
      }
      try {
        const response = await ApiClient.getSearchHistory(sketchId);
        this.getSearchHistory = response.data.objects;
      } catch (e) {
      }
    },

    async updateScenarioTemplates(sketchId) {
      try {
        const response = await ApiClient.getScenarioTemplates(sketchId);
        this.scenarioTemplates = response.data.objects
      } catch (e) {
      }
    },

    async updateSavedGraphs(sketchId) {
      if (!sketchId) {
        sketchId = this.sketch.id;
      }
      try {
        const response = await ApiClient.getSavedGraphList(sketchId);
        this.savedGraphs = response.data.objects[0] || [];
      } catch (e) {
        console.error(e)
      }
    },

    async updateGraphPlugins() {
      try {
        const response = await ApiClient.getGraphPluginList();
        this.graphPlugins = response.data;
      } catch (e) {
      }
    },

    async updateContextLinks() {
      try {
        const response = await ApiClient.getContextLinkConfig();
        this.contextLinkConf = response.data;
      } catch (e) {
      }
    },

    async updateAnalyzerList(sketchId) {
      if (!sketchId) {
        sketchId = this.sketch.id
      }
      try {
        const response = await ApiClient.getAnalyzers(sketchId);
        let analyzerList = {}
        if (response.data !== undefined) {
          response.data.forEach((analyzer) => {
            analyzerList[analyzer.name] = analyzer
          })
        }
        this.sketchAnalyzerList = analyzerList;
      } catch (e) {
        console.error(e)
      }
    },

    async updateSystemSettings() {
      try {
        const response = await ApiClient.getSystemSettings();
        this.systemSettings = response.data || {};
      } catch (e) {
        console.error(e)
      }
    },

    async updateUserSettings() {
      try {
        const response = await ApiClient.getUserSettings();
        this.settings = response.data.objects[0] || {};
      } catch (e) {
        console.error(e)
      }
    },

    setSnackBar(snackbar) {
      this.snackbar = {
        active: true,
        color: snackbar.color,
        message: snackbar.message,
        timeout: snackbar.timeout,
      }
    },
  },
});
