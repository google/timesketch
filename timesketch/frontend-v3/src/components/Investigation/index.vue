<!--
Copyright 2025 Google Inc. All rights reserved.

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
  <v-container class="ai-investigation-canvas pa-0" fluid>
    <Sidebar
      :questions="filteredQuestions"
      :questionsTotal="questionsTotal"
      :completedQuestionsTotal="completedQuestionsTotal"
      :verifiedTotal="verifiedTotal"
      :isLoading="isLoading"
      :reportLocked="store.reportLocked"
      :isGenerating="isGeneratingReport"
    />
    <template v-if="showResultsView">
      <ResultsViewLoader v-if="showLoader" />
      <ResultsView
        :question="selectedQuestion"
        :key="selectedQuestion.id"
        :reportLocked="store.reportLocked"
        :isLoading="isLoading"
      />
    </template>
    <template v-else>
      <ReportViewLoader v-if="showLoader" />
      <ReportView
        v-else
        :reportLocked="store.reportLocked"
        :questions="filteredQuestions"
        :questionsTotal="questionsTotal"
        :completedQuestionsTotal="completedQuestionsTotal"
        :isLoading="isLoading"
      />
    </template>
  </v-container>
  <v-dialog
    transition="dialog-bottom-transition"
    v-model="targetQuestionId"
    width="auto"
  >
    <RemoveQuestionModal
      @close-modal="closeModal"
      :questionId="targetQuestionId"
    />
  </v-dialog>
</template>
<script>
import { useAppStore } from "@/stores/app";
import { useTheme } from "vuetify";
import { useRoute } from "vue-router";
import Sidebar from "./Sidebar";
import RestApiClient from "@/utils/RestApiClient";
import ResultsViewLoader from "./Loaders/ResultsViewLoader.vue";
import LLMAnalyzerService from "./_utils/LLMAnalyzerService";

export default {
  data() {
    return {
      store: useAppStore(),
      route: useRoute(),
      isLoading: false,
      targetQuestionId: null,
      conclusionId: null,
      questions: [],
      showEventLog: false,
      isGeneratingReport: false,
      analyzerService: null,
    };
  },
  created() {
    this.$watch(() => this.route.params.id, this.initializeComponent, {
      immediate: true,
    });
  },
  beforeUnmount() {
    // Clean up the polling when the component is destroyed
    if (this.analyzerService) {
        this.analyzerService.stopPolling();
    }
  },
  methods: {
    async initializeComponent() {
      this.analyzerService = new LLMAnalyzerService(this.store.sketch.id, this.store);
      await this.fetchData();
      this.checkAndResumePolling();
    },

    async checkAndResumePolling() {
      const isRunning = await this.analyzerService.isActive();
      if (isRunning) {
        this.isGeneratingReport = true;
        this.analyzerService._startPolling(
            () => { this.isGeneratingReport = false; this.fetchData(false); },
            () => { this.fetchData(false); }
        );
      }
    },

    async runLogAnalysis() {
      this.isGeneratingReport = true;
      if (this.store.report?.content?.removedQuestions?.length > 0) {
        await this.store.updateReport({ removedQuestions: [] });
      }
      this.analyzerService.startAnalysis(
          // onComplete callback
          () => { this.isGeneratingReport = false; this.fetchData(false); },
          // onUpdate callback
          () => { this.fetchData(false); }
      );
    },

    async deleteAllQuestions() {
      if (!this.filteredQuestions.length) {
        this.store.setNotification({ text: 'There are no questions to remove.', type: 'info' });
        return;
      }
      this.isLoading = true;
      try {
        const allQuestionIds = this.filteredQuestions.map(q => q.id);

        await this.store.updateReport({
          approvedQuestions: [],
          removedQuestions: allQuestionIds,
          conclusionSummaries: [],
        });

        this.store.setActiveQuestion(null);
        this.store.setNotification({
          text: 'All AI-generated questions have been removed.',
          icon: 'mdi-delete-sweep-outline',
          type: 'success',
        });

        await this.fetchData(false);

      } catch (error) {
        console.error('Error removing all questions:', error);
        this.store.setNotification({
          text: 'Failed to remove all questions.',
          icon: 'mdi-alert-circle-outline',
          type: 'error',
        });
      } finally {
        this.isLoading = false;
      }
    },
    confirmDeleteAll() {
      if (window.confirm('Are you sure you want to remove ALL questions from this investigation?')) {
        this.deleteAllQuestions();
      }
    },
    async fetchData(setLoading = true) {
      if (setLoading) {
        this.isLoading = true;
      }
      let questionsArray = [];
      try {
        const [existingQuestions, storyList] =
          await Promise.allSettled([
            RestApiClient.getOrphanQuestions(this.store.sketch.id),
            RestApiClient.getStoryList(this.store.sketch.id),
          ]);

        if (!storyList.value.data.objects[0] || storyList.value.data.objects[0].length < 1) {
          const reportResponse = await RestApiClient.createStory(
            "__ts_investigation_report",
            JSON.stringify([{ type: "__ts_investigation_report" }]),
            this.store.sketch.id,
            ['__ts_investigation_report']
          );
          this.store.report = {
            ...reportResponse.data.objects[0],
            content: JSON.parse(reportResponse.data.objects[0].content),
          };
        } else {
          const existingAiReport = storyList.value.data.objects[0].find(
            ({ title }) => title === "__ts_investigation_report"
          );
          if (existingAiReport) {
            this.store.report = {
              ...existingAiReport,
              content: JSON.parse(existingAiReport.content),
            };
          } else {
            const reportResponse = await RestApiClient.createStory(
              "__ts_investigation_report",
              JSON.stringify([{ type: "__ts_investigation_report" }]),
              this.store.sketch.id,
              ['__ts_investigation_report']
            );
            this.store.report = {
              ...reportResponse.data.objects[0],
              content: JSON.parse(reportResponse.data.objects[0].content),
            };
          }
        }
        const existingQuestionsList =
          existingQuestions.value.data?.objects &&
          existingQuestions.value.data?.objects.length > 0
            ? existingQuestions.value.data.objects[0]
            : [];
        questionsArray = [
          ...existingQuestionsList.map(({ conclusions, ...question }) => ({
            ...question,
            conclusions
          })),
        ];
        this.questions = questionsArray;
      } catch (err) {
        console.error(err);
      } finally {
        if (setLoading) {
          this.isLoading = false;
        }
      }
    },
    addNewQuestion(question) {
      this.questions = [question, ...this.questions];
    },
    updateQuestion(question) {
      this.questions = [
        question,
        ...this.questions.filter(({ id }) => id !== question.id),
      ];
    },
    confirmRemoveQuestion(questionId) {
      this.targetQuestionId = questionId;
    },
    closeModal() {
      this.targetQuestionId = null;
    },
    closeEventLog() {
      this.showEventLog = false;
    },
    async updateObservables(payload) {
      const annotationResponse = await RestApiClient.saveEventAnnotation(
        this.store.sketch.id,
        "label",
        "__ts_fact",
        payload.events,
        null,
        payload.remove,
        payload.conclusionId
      );
      if (
        !annotationResponse.data.objects ||
        annotationResponse.data.objects.length < 1
      ) {
        throw new Error("Unable to update conclusion");
      }
      const currentQuestion = await RestApiClient.getQuestion(
        this.store.sketch.id,
        this.selectedQuestion.id
      );
      this.updateQuestion(currentQuestion.data.objects[0])
      this.store.activeContext.question = currentQuestion.data.objects[0];
    },
    async refreshQuestionById(questionId) {
      // This method fetches a specific question and updates the parent's state.
      try {
        const updatedQuestion = await RestApiClient.getQuestion(
          this.store.sketch.id,
          questionId
        );
        this.updateQuestion(updatedQuestion.data.objects[0]);
        // If the refreshed question is the currently selected one, update activeContext as well
        if (this.selectedQuestion && this.selectedQuestion.id === questionId) {
          this.store.activeContext.question = updatedQuestion.data.objects[0];
        }
      } catch (error) {
        console.error('Error refreshing question by ID:', error);
      }
    },
  },
  computed: {
    showResultsView() {
      return this.selectedQuestion?.id
    },
    showLoader() {
      return this.isLoading || !this.store.report.content
    },
    selectedQuestion() {
      return this.store.activeContext.question;
    },
    filteredQuestions() {
      return this.questions
        ? this.questions.filter(({ id }) => {
            return this.store.report?.content?.removedQuestions
              ? !this.store.report.content.removedQuestions.includes(id)
              : true;
          })
        : []
    },
    questionsTotal() {
      // The total number of questions for progress tracking, excluding rejected ones.
      return this.filteredQuestions?.filter(q => q.status?.status !== 'rejected').length || 0;
    },
    completedQuestionsTotal() {
      return this.filteredQuestions?.filter(({ status }) => status?.status === 'verified').length || 0;
    },
    sketchId() {
      return this.store.sketch.id;
    },
    verifiedTotal() {
      return this.store.reportLocked
        ? this.filteredQuestions.filter(({ id }) =>
            this.store.approvedReportQuestions.includes(id)
          ).length
        : this.questionsTotal;
    },
  },
  provide() {
    return {
      updateObservables: this.updateObservables,
      closeEventLog: this.closeEventLog,
      updateQuestion: this.updateQuestion,
      addNewQuestion: this.addNewQuestion,
      confirmRemoveQuestion: this.confirmRemoveQuestion,
      refreshQuestionById: this.refreshQuestionById,
      runLogAnalysis: this.runLogAnalysis,
      regenerateQuestions: this.fetchData,
      confirmDeleteAll: this.confirmDeleteAll,
      isGeneratingReport: computed(() => this.isGeneratingReport),
    };
  },
  setup() {
    return {
      theme: useTheme(),
    };
  },
};
</script>
