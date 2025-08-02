<!--
Copyright 2025 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
    <FilterBar
    ref="filterBar"
    :questions-total="questionsTotal"
    :questions="questions"
    @filters-changed="handleFiltersChanged"
  />

  <v-list v-if="sortedQuestions" class="report-canvas__questions-list border-thin pa-0 border-b-0 mb-6 rounded-lg">
    <QuestionCard
      v-for="(question, index) in sortedQuestions"
      :key="question.id"
      :value="question"
      :reportLocked="reportLocked"
      v-bind="question"
      :index="index + 1"
      :label="question.labels"
    />
  </v-list>
</template>

<script>
import FilterBar from './FilterBar.vue'

export default {
  components: {
    FilterBar,
  },
  props: {
    questions: Array,
    questionsTotal: Number,
    reportLocked: Boolean,
  },
  inject: ['regenerateQuestions', 'confirmDeleteAll'],
  data() {
    return {
      sortedQuestions: [],
    }
  },
  methods: {
    handleFiltersChanged(filteredQuestions) {
      // Secondary sort to move rejected questions to the bottom,
      // while preserving the primary sort order from the FilterBar within each group.
      const rejected = filteredQuestions.filter(q => q.status?.status === 'rejected');
      const others = filteredQuestions.filter(q => q.status?.status !== 'rejected');

      this.sortedQuestions = [...others, ...rejected];
    },
  },
}
</script>

<style scoped>
.report-canvas__questions-list {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
