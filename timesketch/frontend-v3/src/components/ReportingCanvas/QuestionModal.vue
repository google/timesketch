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
  <v-container fluid class="modal pa-5 rounded-lg">
    <div class="mx-3 mt-3 mb-3">
      <span v-if="isLoading">
        <v-progress-circular
          :size="20"
          :width="1"
          indeterminate
          color="primary"
          class="mr-3"
        ></v-progress-circular>
      </span>

      <div>
        <h3 class="mb-4">Create Question</h3>
        <div class="d-flex align-center mb-8">
          <v-text-field
            v-model="queryString"
            placeholder="Find a question, or create a new one..."
            autofocus
            hide-details
            solo
            :disabled="isLoading"
            variant="outlined"
            @keyup.enter="createQuestion()"
          >
            <v-icon left icon="mdi-magnify" small />
            <v-btn
              depressed
              small
              class="create-question text-none text-uppercase ml-4"
              :disabled="!queryString || isLoading"
              color="primary"
              @click="createQuestion()"
            >
              <template v-if="isLoading">
                Creating Question
                <v-progress-circular
                  :size="20"
                  :width="1"
                  indeterminate
                  class="ml-2"
                ></v-progress-circular>
              </template>
              <template v-else>
                <v-icon left icon="mdi-plus" small />
                Create Question
              </template>
            </v-btn>
          </v-text-field>
        </div>
        <div class="mb-4" v-if="dfigMatches && dfigMatches.length > 0">
          <h4>DFIQ Suggestions ({{ dfigMatches.length }})</h4>
        </div>
        <div class="mb-4" v-if="aiMatches && aiMatches.length > 0">
          <h4>AI-Suggested Questions ({{ aiMatches.length }})</h4>
        </div>

        <div class="dfiq-notice pt-4">
          <p>
            Explore the complete list of DFIQ (Digital Forensics Investigative
            Questions), designed to guide investigations and ensure thorough
            analysis.
          </p>

          <v-btn
            small
            color="primary"
            href="https://dfiq.org/questions"
            target="_external"
          >
            <v-icon left icon="mdi-open-in-new" small />
            Visit DFIQ
          </v-btn>
        </div>
      </div>
    </div>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useAppStore } from "@/stores/app";
import RestApiClient from "@/utils/RestApiClient";

const emit = defineEmits(["close-modal"]);
const queryString = ref(null);
const dfigMatches = ref(null);
const aiMatches = ref(null);
const isLoading = ref(false);
const store = useAppStore();

const addNewQuestion = inject("addNewQuestion");

onMounted(() => {
  fetchDfiqQuestions();
  // fetchAiGeneratedQuestions()
});

const fetchAiGeneratedQuestions = async () => {
  const templates = await RestApiClient.getQuestionTemplates();

  if (templates.objects && templates.objects.length > 0) {
    aiMatches.value = templates.objects;
  }
};

const fetchDfiqQuestions = async () => {
  const templates = await RestApiClient.getQuestionTemplates();

  if (templates.objects && templates.objects.length > 0) {
    dfigMatches.value = templates.objects;
  }
};

const createQuestion = async (template = null) => {
  if (!store.sketch) {
    return;
  }

  isLoading.value = true;

  let questionText = queryString;
  let templateId = null;

  if (template !== null) {
    questionText = template.name;
    templateId = template.id;
  }

  try {
    const question = await RestApiClient.createQuestion(
      store.sketch.id,
      null,
      null,
      questionText.value,
      templateId
    );

    addNewQuestion(question.data.objects[0]);

    store.setNotification({
      text: `You added the question "${question.data.objects[0].name}" to this Sketch`,
      icon: "mdi-plus-circle-outline",
      type: "success",
    });

    // emit("close-modal");
  } catch (error) {
    store.setNotification({
      text: "Unable to add question to this Sketch. Please try again.",
      icon: "mdi-alert-circle-outline",
      type: "error",
    });
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.modal {
  max-width: 700px;
  background-color: #fff;
}

.create-question {
  z-index: 3;
  order: 2;
}

.dfiq-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  border-top: 1px dashed #dadce0;
  font-size: 14px;
}
</style>
