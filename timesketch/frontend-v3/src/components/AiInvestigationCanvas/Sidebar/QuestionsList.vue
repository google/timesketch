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
  <div class="questions-list__bar">
    <h4 class="questions-list__label" v-if="questionsTotal">
      {{ questionsTotal }}
      <span class="font-weight-regular"
        >question{{ questionsTotal > 1 && "s" }}</span
      >
    </h4>

    <div class="filterbar">
      <v-select
        :class="[
          'filterbar__select',
          selectedStatuses.length && 'filterbar__select--active',
        ]"
        color="var(--theme-ai-color-blue-500)"
        :items="['New', 'Pending Review', 'Verified', 'Rejected']"
        v-model="selectedStatuses"
        multiple
        density="compact"
        variant="outlined"
        hide-details
        placeholder="Status"
      >
        <template #selection="{ index }">
          <span v-if="index === 0">
            Status<span v-if="selectedStatuses.length">
              ({{ selectedStatuses.length }})</span
            >
          </span>
        </template>
      </v-select>
    </div>

    <!--
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
    </div>
    -->
  </div>
  <v-list
    v-if="sortedQuestions"
    class="report-canvas__questions-list border-thin pa-0 border-b-0 mb-6 rounded-lg"
  >
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
export default {
  props: {
    questions: Array,
    questionsTotal: Number,
    reportLocked: Boolean,
  },
  inject: ["regenerateQuestions", "confirmDeleteAll"],
  data() {
    return {
      selectedStatuses: [],
    };
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

<style scoped>
.questions-list__label {
  font-size: 14px;
  color: var(--theme-ai-color-black);
  font-weight: 700;

  span {
    color: var(--theme-ai-color-gray-600);
    font-weight: 400;
  }
}

.questions-list__bar {
  padding: 0 0 14px;
}

.report-canvas__questions-list {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.filterbar {
  padding: 14px 0 0;
}

.filterbar__label {
  font-size: 14px;
  font-weight: 500;
  color: var(--theme-ai-color-gray-700);
}

.filterbar__select {
  min-width: 73px;
  width: fit-content !important;
  font-size: 14px;
  font-weight: 500;

  &:deep(.v-field__append-inner),
  &:deep(.v-select__menu-icon) {
    display: none !important;
  }

  &:deep(input::placeholder) {
    opacity: 1 !important;
    color: var(--theme-ai-color-gray-700) !important;
  }

  &:deep(.v-field) {
    padding: 0 !important;
    font-size: 14px;
  }

  &:deep(.v-field__outline) {
    border-radius: 8px;
    color: var(--theme-ai-color-gray-200) !important;
    --v-field-border-opacity: 1;
  }

  &:deep(.v-field__input) {
    --v-input-control-height: 34px;
    --v-field-padding-start: 16px;
    --v-field-padding-end: 16px;
    --v-field-input-padding-top: 0px;
    --v-field-input-padding-bottom: 0px;

    input {
      align-self: center;
      text-align: center;
      left: 0;
    }
  }

  &:deep(.v-select__selection) {
    margin-inline-end: 0 !important;
  }
}

.filterbar__select--active {
  background-color: var(--theme-ai-color-blue-50);
  color: var(--theme-ai-color-blue-700);
}
</style>
