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
  <li class="question mb-10">
    <div class="d-inline-flex align-center justify-start">
      <v-icon
        icon="mdi-check-circle"
        v-if="isApproved"
        small
        color="#34A853"
        class="ml-2"
      />
    </div>
    <p class="text-h6 font-weight-medium">{{ order }}. {{ question.name }}</p>

    <!-- If a custom summary exists, show it -->
    <div v-if="latestConclusionSummary" class="my-4 ml-4">
      <p class="conclusion-summary">{{ latestConclusionSummary }}</p>
    </div>
    <!-- Otherwise, fall back to the list of individual conclusions -->
    <ul
      class="my-4 ml-4"
      v-else-if="question.conclusions && question.conclusions.length > 0"
    >
      <li v-for="conclusion in question.conclusions" :key="conclusion.id">
        <p>{{ conclusion.conclusion }}</p>
      </li>
    </ul>
    <QuestionActionsStrip
      :question="question"
      :reportLocked="reportLocked"
      :isApproved="isApproved"
      variant="approved"
    />
  </li>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  props: { question: Object, index: Number, reportLocked: Boolean },
  inject: ["updateQuestion", "confirmRemoveQuestion"],
  data() {
    return {
      store: useAppStore(),
    };
  },
  computed: {
    isApproved() {
      return !!this.store.report?.content?.approvedQuestions?.find(
        (approvedId) => approvedId === this.question.id
      );
    },
    order() {
      return this.index + 1;
    },
    latestConclusionSummary() {
      const summaries = this.store.report?.content?.conclusionSummaries?.filter(
        (summary) => summary.questionId === this.question.id
      );
      // New summaries are prepended, so the latest is at index 0.
      return summaries?.[0]?.value || null;
    },
  },
};
</script>

<style scoped>
.questions-list {
  list-style: none;
}

.question::marker {
  font-size: inherit;
  font-weight: inherit;
}

.report-form-group {
  display: grid;
  grid-template-columns: 160px 1fr;
  row-gap: 10px;
  column-gap: 20px;
  align-items: center;
}

.report-header {
  background-color: #fafafa;
  border: 1px solid #dcdcdc;
}

.report-auto-timestamp {
  color: #5f6368;
}

.conclusion-summary {
  white-space: pre-line;
}
</style>
