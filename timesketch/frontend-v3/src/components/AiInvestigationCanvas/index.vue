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
        :questionsTotal="questionsTotal"
        :completedQuestionsTotal="completedQuestionsTotal"
        :isLoading="isLoading"
        :questions="filteredQuestions"
      />
      <v-col cols="12" md="6" lg="8" class="fill-height overflow-auto"
        ><!-- TODO: Main content to go here -->
      </v-col>
    </v-row>
  </v-container>
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
      appStore: useAppStore(),
      route: useRoute(),
      isLoading: true,
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
            RestApiClient.llmRequest(this.appStore.sketch.id, "log_analyzer"),
            RestApiClient.getOrphanQuestions(this.appStore.sketch.id),
            RestApiClient.getStoryList(this.appStore.sketch.id),
          ]);

        if (!storyList.value.data.objects || storyList.value.data.objects < 1) {
          const reportResponse = await RestApiClient.createStory(
            "ai-report",
            JSON.stringify([{ type: "ai-report" }]),
            this.appStore.sketch.id
          );

          this.appStore.report = {
            ...reportResponse.value.data.objects[0],
            content: JSON.parse(reportResponse.value.data.objects[0].content),
          };
        } else {
          const existingAiReport = storyList.value.data.objects[0].find(
            ({ title }) => title === "ai-report"
          );

          if (existingAiReport) {
            this.appStore.report = {
              ...existingAiReport,
              content: JSON.parse(existingAiReport.content),
            };
          } else {
            const reportResponse = await RestApiClient.createStory(
              "ai-report",
              JSON.stringify([{ type: "ai-report" }]),
              this.appStore.sketch.id
            );

            this.appStore.report = {
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
  },
  computed: {
    filteredQuestions() {
      return this.questions
        ? this.questions.filter(({ id }) => {
            return this.appStore.report.content.removedQuestions
              ? !this.appStore.report.content.removedQuestions.includes(id)
              : true;
          })
        : [];
    },
    questionsTotal() {
      return this.filteredQuestions?.length;
    },
    completedQuestionsTotal() {
      return this.appStore.report?.content?.approvedQuestions?.length || 0;
    },
    sketchId() {
      return this.appStore.sketch.id;
    },
  },
  provide() {
    return {
      regenerateQuestions: this.fetchData, // TODO: Revisit this once the API is in place for this async op
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
.reporting-canvas {
  height: calc(100vh - 65px);
  overflow: hidden;
}

.reporting-canvas__sidebar {
  display: grid;
  grid-template-rows: auto 1fr;
}
</style>
