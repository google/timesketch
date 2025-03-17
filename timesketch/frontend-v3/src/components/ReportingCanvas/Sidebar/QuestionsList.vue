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
  <div class="d-flex justify-space-between px-2">
    <h4 class="mb-2">
      {{ questionsTotal }} <span class="font-weight-regular">questions</span>
    </h4>
    <v-btn
      variant="text"
      size="small"
      color="primary"
      @click="setShowModal"
    >
      <v-icon icon="mdi-plus" left small />
      Create Question</v-btn
    >
  </div>
  <v-list
    v-if="sortedQuestions"
    class="report-canvas__questions-list border-thin pa-0 border-b-0 mb-6 rounded-lg"
  >
    <QuestionCard
      v-for="question in sortedQuestions"
      :key="question"
      :value="question"
      v-bind="question"
    />
  </v-list>
  <div class="p-2 text-center">
    <p class="mb-2">
      Before regenerating, review existing questions. Previous unsaved questions
      will remain, and new ones will be added.
    </p>

    <v-btn
      variant="text"
      size="small"
      color="primary"
      @click="regenerateQuestions()"
      class="text-uppercase"
    >
      <v-icon icon="mdi-reload" class="mr-2" left small />
      Regenerate Questions</v-btn
    >
  </div>
</template>

<script>
export default {
  props: {
    questions: Array,
    questionsTotal: Number,
  },
  data() {
    return {
      showModal: false,
    };
  },
  methods: {
    setShowModa() {
      this.showModal.value = !this.showModal.value;
    },
  },
  inject: ['regenerateQuestions'],
  computed: {
    sortedQuestions() {
      return this.questions && this.questions.length > 0
        ? [
            ...this.questions.sort(
              (a, b) => new Date(b.updated_at) - new Date(a.updated_at)
            ),
          ]
        : [];
    },
  },
};
</script>

<style scoped>
.report-canvas__questions-list {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
