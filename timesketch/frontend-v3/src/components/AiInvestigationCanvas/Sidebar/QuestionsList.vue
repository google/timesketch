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
  <div class="d-flex justify-space-between align-center px-2">
    <h4 class="mb-2" v-if="questionsTotal">
      {{ questionsTotal }}
      <span class="font-weight-regular"
        >question{{ questionsTotal > 1 && "s" }}</span
      >
    </h4>
    <div class="d-flex ga-2">
      <v-btn
        variant="text"
        size="small"
        color="error"
        @click="confirmDeleteAll"
        :disabled="reportLocked || questionsTotal === 0"
        title="Remove all questions (for testing)"
      >
        <v-icon icon="mdi-delete-sweep-outline" left small />
        Remove All
      </v-btn>
      <v-btn
        variant="text"
        size="small"
        color="primary"
        @click="toggleModal"
        :disabled="reportLocked"
      >
        <v-icon icon="mdi-plus" left small />
        Create Question</v-btn
      >
    </div>
  </div>
  <v-list
    v-if="sortedQuestions"
    class="report-canvas__questions-list border-thin pa-0 border-b-0 mb-6 rounded-lg"
  >
    <QuestionCard
      v-for="(question,index) in sortedQuestions"
      :key="question.id"
      :value="question"
      :reportLocked="reportLocked"
      v-bind="question"
      :index="index + 1"
    />
  </v-list>
  <v-dialog
    transition="dialog-bottom-transition"
    v-model="showModal"
    width="auto"
  >
    <AddQuestionModal @close-modal="toggleModal" />
  </v-dialog>
</template>

<script>
export default {
  props: {
    questions: Array,
    questionsTotal: Number,
    reportLocked: Boolean,
  },
  data() {
    return {
      showModal: false,
    };
  },
  inject: ["regenerateQuestions", "confirmDeleteAll"],
  methods: {
    toggleModal() {
      this.showModal = !this.showModal;
    },
  },
  computed: {
    sortedQuestions() {
      if (!this.questions || this.questions.length === 0) {
        return [];
      }
      return [...this.questions].sort((a, b) => a.id - b.id);
    },
  },
};
</script>

<style>
.report-canvas__questions-list {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
