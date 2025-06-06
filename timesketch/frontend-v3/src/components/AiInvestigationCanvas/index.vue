<!--
Copyright 2025 Google Inc. All rights reserved.

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
  <v-container class="ai-investigation-canvas grid pa-0" fluid>
    <v-row no-gutters class="fill-height overflow-hidden">
      <Sidebar
        :questions="filteredQuestions"
        :questionsTotal="questionsTotal"
        :completedQuestionsTotal="completedQuestionsTotal"
        :verifiedTotal="verifiedTotal"
        :isLoading="isLoading"
        :reportLocked="store.reportLocked"
      />
      <v-col cols="12" md="6" lg="8" class="fill-height overflow-auto">
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
      </v-col>
    </v-row>
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
      pollingInterval: null,
      isGeneratingReport: false,
    };
  },
  created() {
    this.$watch(() => this.route.params.id, this.fetchData, {
      immediate: true,
    });
  },
  methods: {
    // NEW: Method specifically for running the log analyzer
    runLogAnalysis() {
      if (this.questions.length === 0) {
        this.isLoading = true;
      }
      this.isGeneratingReport = true;
      this.store.setNotification({
        text: 'AI analysis has started. Findings will appear as they are discovered.',
        icon: 'mdi-clock-start',
        type: 'info',
      });
      // 1. "Fire" the request but DON'T await it here.
      const analysisPromise = RestApiClient.llmRequest(this.store.sketch.id, 'log_analyzer');
      // Set a brief timeout to allow the initial loader to show before polling starts
      setTimeout(() => {
        this.isLoading = false;
        if (this.pollingInterval) clearInterval(this.pollingInterval);
        this.pollingInterval = setInterval(() => {
          this.fetchData(false);
        }, 5000);
      }, 1000)
      // 3. Handle the final completion of the long request.
      analysisPromise.then(() => {
        this.store.setNotification({
          text: 'AI analysis complete. All questions have been generated.',
          icon: 'mdi-check-circle-outline',
          type: 'success',
        });
      }).catch(error => {
        this.store.setNotification({
          text: 'An error occurred during AI analysis. Please check the logs.',
          icon: 'mdi-alert-circle-outline',
          type: 'error',
        });
        console.error('Error running log analyzer:', error);
      }).finally(() => {
        if (this.pollingInterval) clearInterval(this.pollingInterval);
        this.pollingInterval = null;
        this.isGeneratingReport = false;
        this.fetchData(true);
      });
    },
    async deleteAllQuestions() {
      if (!this.questions.length) {
        this.store.setNotification({ text: 'There are no questions to remove.', type: 'info' });
        return;
      }
      this.isLoading = true;
      try {
        const allQuestionIds = this.questions.map(q => q.id);
        // Update the report to mark all questions as removed and clear approved list
        await this.store.updateReport({
          approvedQuestions: [],
          removedQuestions: allQuestionIds,
          conclusionSummaries: [], // Also clear any saved conclusion summaries
        });
        // Clear the local state to update the UI instantly
        this.questions = [];
        this.store.setActiveQuestion(null);
        this.store.setNotification({
          text: 'All AI-generated questions have been removed.',
          icon: 'mdi-delete-sweep-outline',
          type: 'success',
        });
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
        
        // This check was slightly incorrect, it should be .length
        if (!storyList.value.data.objects[0] || storyList.value.data.objects[0].length < 1) {
          const reportResponse = await RestApiClient.createStory(
            "ai-report",
            JSON.stringify([{ type: "ai-report" }]),
            this.store.sketch.id
          );
          this.store.report = {
            ...reportResponse.data.objects[0],
            content: JSON.parse(reportResponse.data.objects[0].content),
          };
        } else {
          const existingAiReport = storyList.value.data.objects[0].find(
            ({ title }) => title === "ai-report"
          );
          if (existingAiReport) {
            this.store.report = {
              ...existingAiReport,
              content: JSON.parse(existingAiReport.content),
            };
          } else {
            const reportResponse = await RestApiClient.createStory(
              "ai-report",
              JSON.stringify([{ type: "ai-report" }]),
              this.store.sketch.id
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
        : [];
    },
    questionsTotal() {
      return this.filteredQuestions?.length || 0;
    },
    completedQuestionsTotal() {
      // Logic correction: Should check approvedQuestions
      return this.filteredQuestions?.filter(({id}) => this.store.report?.content?.approvedQuestions?.includes(id)).length || 0
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
      // NEW: Provide the new method to child components
      runLogAnalysis: this.runLogAnalysis,
      // Renamed for clarity
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
<style scoped>
.ai-investigation-canvas {
  height: calc(100vh - 65px);
  overflow: hidden;
}
.ai-investigation-canvas__sidebar {
  display: grid;
  grid-template-rows: auto auto 1fr;
}
</style>
