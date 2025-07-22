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
  <v-card v-if="isGenerating" class="progress-card" :elevation="0">
    <div class="flex-1-0">
      <div class="d-flex justify-space-between">
        <h4 v-if="questionsTotal" class="mb-2">
          AI Analysis in progress: Processing results ...
        </h4>
        <h4 v-else class="mb-2">AI Analysis in progress: Sending events ...</h4>
        <p v-if="questionsTotal">
          <span class="font-weight-bold">{{ questionsTotal }}</span>
          questions created
        </p>
      </div>
      <v-progress-linear
        height="12"
        color="primary"
        indeterminate
        rounded="xl"
      ></v-progress-linear>
    </div>
    <v-card-actions class="flex-0-0 pa-0">
      <v-spacer></v-spacer>
      <v-btn
        variant="outlined"
        class="ai-inline-cta"
        @click="toggleModal"
        :disabled="reportLocked || questionsTotal === 0"
      >
        Create Question
      </v-btn>
    </v-card-actions>
  </v-card>
  <v-card v-else class="progress-card" :elevation="0">
    <div class="flex-grow-1">
      <div
        class="d-flex justify-space-between ga-1 align-baseline mb-2 flex-wrap"
      >
        <h4>Progress</h4>
        <p v-if="questionsTotal" class="text-body-2 text-no-wrap">
          <span class="font-weight-bold"
            >{{ completedQuestionsTotal }} / {{ questionsTotal }}</span
          >
          questions finalized
        </p>
      </div>
      <v-progress-linear
        class="progress-card__bar"
        height="12"
        width="100%"
        color="var(--theme-ai-color-ts-blue)"
        bg-color="var(--theme-ai-color-blue-100)"
        bg-opacity="1"
        :model-value="percentageCompleted"
        rounded="xl"
      ></v-progress-linear>
    </div>
    <v-card-actions class="flex-0-0 pa-0 h-auto progress-card__cta">
      <v-btn
        variant="outlined"
        class="ai-inline-cta"
        @click="toggleModal"
        :disabled="reportLocked || questionsTotal === 0"
      >
        Create Question
      </v-btn>
    </v-card-actions>
  </v-card>
  <v-dialog
    transition="dialog-bottom-transition"
    v-model="showModal"
    width="auto"
  >
    <AddQuestionModal @close-modal="toggleModal" />
  </v-dialog>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  data() {
    return {
      store: useAppStore(),
      showModal: false,
    };
  },
  props: {
    questionsTotal: Number,
    completedQuestionsTotal: Number,
    isGenerating: Boolean,
    reportLocked: Boolean,
  },
  methods: {
    toggleModal() {
      this.showModal = !this.showModal;
    },
  },
  computed: {
    percentageCompleted() {
      return this.questionsTotal
        ? (this.completedQuestionsTotal / this.questionsTotal) * 100
        : 0;
    },
  },
};
</script>
<style scoped>
.progress-card {
  padding: 17px 20px 16px;
  border-radius: 8px;
  border: 1px solid var(--theme-ai-color-gray-100);
  background-color: var(--theme-ai-color-white);
  margin-bottom: 16px;
  gap: 30px;
  display: flex;
  flex-wrap: nowrap;
  justify-content: center;
}

.progress-card__cta {
  min-height: auto;
}

.progress-card__bar {
  &:deep(.v-progress-linear__determinate) {
    border-radius: 24px;
  }
}
</style>
