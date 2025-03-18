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
  <v-container class="reporting-canvas grid pa-0" fluid>
    <v-row no-gutters class="fill-height overflow-hidden">
      <Sidebar
        :questions="filteredQuestions"
        :questionsTotal="questionsTotal"
        :completedQuestionsTotal="completedQuestionsTotal"
        :isLoading="isLoading"
        :reportLocked="reportLocked"
      />
      <v-col
        cols="12"
        md="6"
        lg="8"
        class="fill-height overflow-auto pa-4"
        v-if="isLoading"
      >
        <v-skeleton-loader height="60" class="mb-2"></v-skeleton-loader>

        <div class="d-flex justify-space-between mb-10">
          <v-skeleton-loader
            height="20"
            width="80"
            class="ma-0"
          ></v-skeleton-loader>
          <div class="d-flex justify-space-between mb-5">
            <v-skeleton-loader
              height="20"
              width="95"
              class="mr-5"
            ></v-skeleton-loader>
            <v-skeleton-loader
              height="20"
              width="240"
              class="ma-0"
            ></v-skeleton-loader>
          </div>
        </div>

        <div class="d-flex mb-3 ga-4">
          <v-skeleton-loader
            height="40"
            width="100"
            class="ma-0"
          ></v-skeleton-loader>
          <v-skeleton-loader
            height="40"
            width="500"
            class="ma-0"
          ></v-skeleton-loader>
        </div>
        <div class="d-flex mb-3 ga-4">
          <v-skeleton-loader
            height="40"
            width="100"
            class="ma-0"
          ></v-skeleton-loader>
          <v-skeleton-loader
            height="40"
            width="500"
            class="ma-0"
          ></v-skeleton-loader>
        </div>
        <div class="d-flex mb-3 ga-4">
          <v-skeleton-loader
            height="40"
            width="100"
            class="ma-0"
          ></v-skeleton-loader>
          <v-skeleton-loader
            height="40"
            width="500"
            class="ma-0"
          ></v-skeleton-loader>
        </div>
        <div class="d-flex mb-15 ga-4">
          <v-skeleton-loader
            height="40"
            width="100"
            class="ma-0"
          ></v-skeleton-loader>
          <v-skeleton-loader
            height="40"
            width="500"
            class="ma-0"
          ></v-skeleton-loader>
        </div>

        <div class="d-flex justify-space-between align-center mb-3 ga-4">
          <v-skeleton-loader
            height="20"
            width="100"
            class="mb-5"
          ></v-skeleton-loader>
          <v-skeleton-loader
            height="20"
            width="220"
            class="mb-5"
          ></v-skeleton-loader>
        </div>

        <v-skeleton-loader height="172" class="mb-10"></v-skeleton-loader>
        <v-skeleton-loader height="172" class="mb-5"></v-skeleton-loader>
        <v-skeleton-loader height="172" class="mb-5"></v-skeleton-loader>
        <v-skeleton-loader height="172" class="mb-5"></v-skeleton-loader>
        <v-skeleton-loader height="172" class="mb-5"></v-skeleton-loader>
      </v-col>
      <v-col v-else cols="12" md="6" lg="8" class="fill-height overflow-auto">
        <ResultsView
          v-if="selectedQuestion && selectedQuestion.id"
          :question="selectedQuestion"
          :key="selectedQuestion.id"
          :reportLocked="reportLocked"
        />
        <ReportView
          v-else
          :questions="filteredQuestions"
          :questionsTotal="questionsTotal"
          :completedQuestionsTotal="completedQuestionsTotal"
          :summary="metadata ? metadata.summary : ''"
          :reportLocked="reportLocked"
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
import { debounce } from "lodash";

export default {
  props: {
    question: Object,
    reportLocked: Boolean,
  },
  inject: ["updateQuestion", "confirmRemoveQuestion"],
  data() {
    return {
      store: useAppStore(),
      showModal: false,
      isConfirming: false,
      riskLevel: this.question.riskLevel,
      conclusion: this.question.conclusion,
    };
  },
  computed: {
    completed() {
      let isApproved = false;

      if (
        this.store.report?.content?.approvedQuestions &&
        store.report?.content?.approvedQuestions.length > 0
      ) {
        isApproved = !!this.store.report.content.approvedQuestions.find(
          (approvedId) => approvedId === this.question.id
        );
      }

      return isApproved;
    },
  },
  methods: {
    async regenerateConclusion() {
      // TODO : Implement when API work is completed
    },
    async downloadReport() {
      // TODO : Implement when API work is completed
    },
    async confirmAndSave() {
      isConfirming.value = true;

      try {
        const existingQuestions =
          store.report?.content?.approvedQuestions || [];

        await store.updateReport({
          approvedQuestions: new Set([...existingQuestions, question.id]),
        });

        store.setNotification({
          text: `Question approved`,
          icon: "mdi-check-circle-outline",
          type: "success",
        });
      } catch (error) {
        store.setNotification({
          text: `Unable to approve question`,
          icon: "mdi-close-circle-outline",
          type: "error",
        });
      } finally {
        isConfirming.value = false;
      }
    },
  },
  watch: {
    conclusion: debounce(async function (conclusion) {
      const response = await RestApiClient.createQuestionConclusion(
        store.sketch.id,
        question.id,
        conclusion
      );

      updateQuestion({
        ...response.data.objects[0],
        conclusion:
          response.data.objects[0].conclusions?.length > 0
            ? response.data.objects[0].conclusions
                .map(({ conclusion }) => conclusion)
                .join()
            : "",
      });
    }, 200),
    riskLevel(riskLevel) {
      this.updateQuestion({ ...this.question, riskLevel });
      this.store.setActiveQuestion({ ...this.question, riskLevel });
    },
  },
};
</script>

<style scoped>
.reporting-canvas {
  height: calc(100vh - 65px);
  overflow: hidden;
}
</style>
