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
  <v-col
    cols="12"
    md="6"
    lg="4"
    class="ai-investigation-canvas__sidebar bg-grey-lighten-4 pa-4 fill-height overflow-hidden"
  >
    <QuestionsListLoader v-if="isLoading" />
    <template v-else>
      <div>
        <h2 class="mb-5 h5">Questions</h2>
        <QuestionsProgress
          :questionsTotal="questionsTotal"
          :completedQuestionsTotal="completedQuestionsTotal"
        />
      </div>

      <QuestionsListLoader v-if="isLoading" />
      <QuestionsList :questions="sortedQuestions" :questionsTotal="questionsTotal" :reportLocked="reportLocked"
    /></template>
  </v-col>
</template>

<script>
export default {
  props: {
    questionsTotal: {
      type: Number,
      default: 0,
    },
    completedQuestionsTotal: {
      type: Number,
      default: 0,
    },
    isLoading: {
      type: Boolean,
      default: true,
    },
    questions: Array,
    reportLocked: Boolean,
  },
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
.ai-investigation-canvas__sidebar {
  display: grid;
  grid-template-rows: auto auto 1fr auto;
}
</style>
