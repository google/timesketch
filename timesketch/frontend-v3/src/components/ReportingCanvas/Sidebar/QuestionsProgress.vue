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
      />
      <v-col cols="12" md="6" lg="8" class="fill-height overflow-auto"> </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { useAppStore } from "@/stores/app";
import RestApiClient from "@/utils/RestApiClient";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import Sidebar from "./Sidebar";
import RemoveQuestionModal from "./Modals/RemoveQuestionModal";
import { storeToRefs } from "pinia";

const store = useAppStore();
const route = useRoute();
const metadata = ref(null);
const questions = ref([]);
const isLoading = ref(true);
const targetQuestionId = ref(null);

const { activeQuestion } = storeToRefs(store);
const { reportLocked } = storeToRefs(store);

const filteredQuestions = computed(() => {
  return questions.value
    ? questions.value.filter(({ id }) => {
        return store.report.content.removedQuestions
          ? !store.report.content.removedQuestions.includes(id)
          : true;
      })
    : [];
});

const questionsTotal = computed(() => filteredQuestions?.value?.length);
const selectedQuestion = activeQuestion;

const completedQuestionsTotal = computed(
  () => store.report?.content?.approvedQuestions?.length || 0
);

const closeModal = () => {
  targetQuestionId.value = null;
};

watch(() => route.params.sketchId, fetchData, { immediate: true });

provide("updateQuestion", (question) => {
  questions.value = [
    question,
    ...questions.value.filter(({ id }) => id !== question.id),
  ];
});

provide("addNewQuestion", (question) => {
  questions.value = [question, ...questions.value];
});

provide("confirmRemoveQuestion", (questionId) => {
  targetQuestionId.value = questionId;
});

provide("fileReport", (questionId) => {
  targetQuestionId.value = questionId;
});

provide("regenerateQuestions", async () => {
  isLoading.value = true;

  try {
    await Promise.all([
      await RestApiClient.llmRequest(store.sketch.id, "log_analyzer"),
      await RestApiClient.getOrphanQuestions(store.sketch.id),
    ]);

    store.setNotification({
      text: `You successfully regenerated the questions`,
      icon: "mdi-plus-circle-outline",
      type: "success",
    });
  } catch (error) {
    store.setNotification({
      text: `Unable to regenerate questions`,
      icon: "mdi-check-circle-outline",
      type: "error",
    });
  } finally {
    isLoading.value = false;
  }
});

async function fetchData() {
  isLoading.value = true;
  let questionsArray = [];

  try {
    const [aiQuestions, existingQuestions, storyList] =
      await Promise.allSettled([
        RestApiClient.llmRequest(store.sketch.id, "log_analyzer"),
        RestApiClient.getOrphanQuestions(store.sketch.id),
        RestApiClient.getStoryList(store.sketch.id),
      ]);

    if (!storyList.value.data.objects || storyList.value.data.objects < 1) {
      const reportResponse = await RestApiClient.createStory(
        "ai-report",
        JSON.stringify([{ type: "ai-report" }]),
        store.sketch.id
      );

      store.report = {
        ...reportResponse.value.data.objects[0],
        content: JSON.parse(reportResponse.value.data.objects[0].content),
      };
    } else {
      const existingAiReport = storyList.value.data.objects[0].find(
        ({ title }) => title === "ai-report"
      );

      if (existingAiReport) {
        store.report = {
          ...existingAiReport,
          content: JSON.parse(existingAiReport.content),
        };
      } else {
        const reportResponse = await RestApiClient.createStory(
          "ai-report",
          JSON.stringify([{ type: "ai-report" }]),
          store.sketch.id
        );

        store.report = {
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
      questionsArray = [...questionsArray, ...aiQuestions.value.data.questions];
    }

    questions.value = questionsArray;
  } catch (err) {
    console.error(err);

    store.setNotification({
      text: `Unable to retrieve questions`,
      icon: "mdi-plus-circle-outline",
      type: "error",
    });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.reporting-canvas {
  height: calc(100vh - 65px);
  overflow: hidden;
}
</style>
