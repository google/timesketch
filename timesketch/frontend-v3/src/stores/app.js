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

import ApiClient from "../utils/RestApiClient.js";
import { defineStore } from "pinia";


export const ReportStatus = Object.freeze({
  VERIFIED: 'VERIFIED',
  UNVERIFIED: 'UNVERIFIED'
})

export const useAppStore = defineStore("app", {
  state: () => ({
    sketch: {},
    meta: {},
    searchHistory: {},
    timeFilters: {},
    report: {},
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
      story: {
        filed: false,
      },
    },
    snackbar: {
      active: false,
      color: "",
      message: "",
      timeout: -1,
    },
    contextLinkConf: {},
    sketchAnalyzerList: {},
    savedVisualizations: [],
    activeAnalyses: [],
    analyzerResults: [],
    enabledTimelines: [],
    notification: null,
    sketchAccessDenied: false,
  }),
  actions: {
    async setAppStore() { },

    resetState() {
      ApiClient.getLoggedInUser().then((response) => {
        let currentUser = response.data.objects[0].username;
        this.$reset();
        this.currentUser = currentUser;
      });
    },

    async updateReport(payload) {
      const newContent = {
        ...this.report.content,
        ...payload,
      };

      this.report = {
        ...this.report,
        content: newContent,
      };

      await ApiClient.updateStory(
        this.report.title,
        JSON.stringify(newContent),
        this.sketch.id,
        this.report.id
      );
    },

    setActiveQuestion(question) {
      this.activeContext = {
        ...this.activeContext,
        question
      }
    },

    setNotification(notification) {
      this.notification = notification
    },

    async updateSketch(sketchId) {
      this.sketchAccessDenied = false;
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
        if (e.response && e.response.status === 403) {
          this.sketchAccessDenied = true;
        } else {
          console.error(e);
        }
      }
    },

    async updateTimelineTags(sketchId) {
      // Don't fetch Tag data on archived sketches.
      if (this.sketch.status?.[0]?.status === 'archived') {
        this.tags = []
        return
      }

      if (!this.sketch.active_timelines.length) {
        return;
      }
      let formData = {
        aggregator_name: "field_bucket",
        aggregator_parameters: {
          field: "tag",
          limit: "1000",
        },
      };
      try {
        const response = await ApiClient.runAggregator(sketchId, formData);
        this.tags = response.data.objects[0]["field_bucket"]["buckets"];
      } catch (e) { }
    },

    async updateDataTypes(sketchId) {
      if (this.sketch.status?.[0]?.status === 'archived') {
        this.dataTypes = []
        return
      }

      if (!this.sketch.active_timelines.length) {
        return;
      }
      let formData = {
        aggregator_name: "field_bucket",
        aggregator_parameters: {
          field: "data_type",
          limit: "1000",
        },
      };

      try {
        const response = await ApiClient.runAggregator(sketchId, formData);
        this.dataTypes = response.data.objects[0]["field_bucket"]["buckets"];
      } catch (e) { }
    },

    async updateEventLabels({ label: inputLabel, num }) {
      if (!inputLabel || !num) {
        return;
      }
      let allLabels = this.meta.filter_labels;
      let label = allLabels.find((label) => label.label === inputLabel);
      if (label !== undefined) {
        label.count += num;
      } else {
        allLabels.push({ label: inputLabel, count: num });
      }
      this.meta.filter_labels = allLabels;
    },

    async updateSearchHistory(sketchId) {
      if (!sketchId) {
        sketchId = this.sketch.id;
      }
      try {
        const response = await ApiClient.getSearchHistory(sketchId);
        this.getSearchHistory = response.data.objects;
      } catch (e) { }
    },

    async updateTimeFilters(sketchId) {
      if (!sketchId) {
        sketchId = this.sketch.id
      }
      try {
        const response = await ApiClient.getSearchHistoryTree(sketchId)
        const treeData = response.data.objects[0]
        const timeFilters = []

        function parseNode(node) {
          if (!node || !node.query_filter) {
            return
          }
          const qf = JSON.parse(node.query_filter)
          if (qf.chips.length > 0) {
            timeFilters.push(...(qf.chips.filter(c => c.type === 'datetime_range')))
          }
          for (let c of node.children) {
            parseNode(c)
          }
        }

        if (treeData) {
          parseNode(treeData)
        }

        const deduped = []
        const timeFiltersSet = new Set()
        for (let tf of timeFilters) {
          if (!timeFiltersSet.has(tf.value)) {
            timeFiltersSet.add(tf.value)
            deduped.push(tf)
          }
        }
        deduped.reverse()

        this.timeFilters = deduped
      } catch (e) {
        console.error(e)
      }
    },

    async updateScenarioTemplates(sketchId) {
      try {
        const response = await ApiClient.getScenarioTemplates(sketchId);
        this.scenarioTemplates = response.data.objects;
      } catch (e) { }
    },

    async updateSavedGraphs(sketchId) {
      if (!sketchId) {
        sketchId = this.sketch.id;
      }
      try {
        const response = await ApiClient.getSavedGraphList(sketchId);
        this.savedGraphs = response.data.objects[0] || [];
      } catch (e) {
        console.error(e);
      }
    },

    async updateGraphPlugins() {
      try {
        const response = await ApiClient.getGraphPluginList();
        this.graphPlugins = response.data;
      } catch (e) { }
    },

    async updateContextLinks() {
      try {
        const response = await ApiClient.getContextLinkConfig();
        this.contextLinkConf = response.data;
      } catch (e) { }
    },

    async updateAnalyzerList(sketchId) {
      if (!sketchId) {
        sketchId = this.sketch.id;
      }
      try {
        const response = await ApiClient.getAnalyzers(sketchId);
        let analyzerList = {};
        if (response.data !== undefined) {
          response.data.forEach((analyzer) => {
            analyzerList[analyzer.name] = analyzer;
          });
        }
        this.sketchAnalyzerList = analyzerList;
      } catch (e) {
        console.error(e);
      }
    },

    async updateSystemSettings() {
      try {
        const response = await ApiClient.getSystemSettings();
        this.systemSettings = response.data || {};
      } catch (e) {
        console.error(e);
      }
    },

    async updateUserSettings() {
      try {
        const response = await ApiClient.getUserSettings();
        this.settings = response.data.objects[0] || {};
      } catch (e) {
        console.error(e);
      }
    },

    setSnackBar(snackbar) {
      this.snackbar = {
        active: true,
        color: snackbar.color,
        message: snackbar.message,
        timeout: snackbar.timeout,
      };
    },

    async updateEnabledTimelines(timelines) {
      this.enabledTimelines = timelines;
    },

    async toggleEnabledTimeline(payload) {
      if (this.enabledTimelines.includes(payload)) {
        this.enabledTimelines = this.enabledTimelines.filter(
          (tl) => payload !== tl
        );
      } else {
        const freshEnabledTimelines = [...this.enabledTimelines, payload];
        this.enabledTimelines = freshEnabledTimelines;
      }
    },
  },
  getters: {
    activeQuestion() {
      return this.activeContext.question;
    },
    summary() {
      return this.report?.content?.summary;
    },
    reportLocked() {
      return this.report?.content?.status === ReportStatus.VERIFIED;
    },
    approvedReportQuestions() {
      return this.report?.content?.approvedQuestions ?? [];

    },
    removedReportQuestions() {
      return this.report?.content?.removedQuestions ?? [];
    },
  },
});
