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
        :isLoading="isLoading"
        :reportLocked="store.reportLocked"
      />
      <v-col cols="12" md="6" lg="8" class="fill-height overflow-auto">
        <ResultsView
          v-if="selectedQuestion && selectedQuestion.id"
          :question="selectedQuestion"
          :key="selectedQuestion.id"
          :reportLocked="store.reportLocked"
        />
        <ReportView
          v-else
          :isLoading="isLoading"
          :reportLocked="store.reportLocked"
          :questions="filteredQuestions"
          :questionsTotal="questionsTotal"
          :completedQuestionsTotal="completedQuestionsTotal"
          :summary="metadata ? metadata.summary : ''"
        />
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

export default {
  data() {
    return {
      store: useAppStore(),
      route: useRoute(),
      isLoading: false,
      targetQuestionId: null,
      questions: [],
    };
  },
  created() {
    this.$watch(() => this.route.params.id, this.fetchData, {
      immediate: true,
    });
  },
  methods: {
    async fetchData() {
      // TODO revist once the API work has been completed
      this.isLoading = true;
      let questionsArray = [];

      try {
        const [aiQuestions, existingQuestions, storyList] =
          await Promise.allSettled([
            RestApiClient.llmRequest(this.store.sketch.id, "log_analyzer"),
            RestApiClient.getOrphanQuestions(this.store.sketch.id),
            RestApiClient.getStoryList(this.store.sketch.id),
          ]);

        if (!storyList.value.data.objects || storyList.value.data.objects < 1) {
          const reportResponse = await RestApiClient.createStory(
            "ai-report",
            JSON.stringify([{ type: "ai-report" }]),
            this.store.sketch.id
          );

          this.store.report = {
            ...reportResponse.value.data.objects[0],
            content: JSON.parse(reportResponse.value.data.objects[0].content),
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
              ...reportResponse.value.data.objects[0],
              content: JSON.parse(reportResponse.value.data.objects[0].content),
            };
          }
        }

        const existingQuestionsList =
          existingQuestions.value.data.objects &&
          existingQuestions.value.data.objects.length > 0
            ? existingQuestions.value.data.objects[0]
            : [];

        questionsArray = [
          ...existingQuestionsList.map(({ conclusions, ...question }) => ({
            ...question,
            conclusion:
              conclusions?.length > 0
                ? conclusions.map(({ conclusion }) => conclusion).join()
                : "",
          })),
        ];

        if (
          aiQuestions.status === "fulfilled" &&
          aiQuestions?.value?.data?.questions
        ) {
          metadata.value = aiQuestions.value.data.meta;
          questionsArray = [
            ...questionsArray,
            ...aiQuestions.value.data.questions,
          ];
        }
        this.questions = questionsArray;
      } catch (err) {
        console.error(err);
      } finally {
        this.isLoading = false;
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
  },
  computed: {
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
      console.log(this.filteredQuestions?.length);

      return this.filteredQuestions?.length || 0;
    },
    completedQuestionsTotal() {
      return this.store.report?.content?.approvedQuestions?.length || 0;
    },
    sketchId() {
      return this.store.sketch.id;
    },
  },
  provide() {
    return {
      updateQuestion: this.updateQuestion,
      addNewQuestion: this.addNewQuestion,
      confirmRemoveQuestion: this.confirmRemoveQuestion,
      regenerateQuestions: this.fetchData,
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
  grid-template-rows: auto auto 1fr auto;
}
</style>
