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
      <div class="conclusion-summary" v-html="renderedSummary"></div>
    </div>
    <!-- Otherwise, fall back to a call to action to review the question -->
    <div v-else class="my-4 ml-4 font-italic text-body-2">
      <p v-if="question.conclusions && question.conclusions.length > 0">
        TODO: No answer has been provided for this question yet.
        <a href="#" @click.prevent="setActiveQuestion">
          Review the conclusions and add your answer.
        </a>
      </p>
      <p v-else>
        TODO: No answer has been provided for this question yet.
        <a href="#" @click.prevent="setActiveQuestion">
          Add your conclusion and answer to this question.
        </a>
      </p>
    </div>
    <QuestionActionsStrip
      :question="question"
      :reportLocked="reportLocked"
      :isApproved="isApproved"
      variant="compact"
      :index="index"
    />
  </li>
</template>

<script>
import { useAppStore } from "@/stores/app";
import { marked } from "marked";
import DOMPurify from "dompurify";

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
      return this.question?.status?.status === 'verified';
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
    renderedSummary() {
      if (this.latestConclusionSummary) {
        const unsafeHtml = marked(this.latestConclusionSummary);
        return DOMPurify.sanitize(unsafeHtml);
      }
      return "";
    },
  },
  methods: {
    setActiveQuestion() {
      this.store.setActiveQuestion(this.question);
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
  line-height: 1.5;
}

/* Deep selectors to style the content rendered by v-html */
.conclusion-summary :deep(p) {
  margin-bottom: 1em;
}
.conclusion-summary :deep(ul),
.conclusion-summary :deep(ol) {
  padding-left: 2em;
  margin-bottom: 1em;
}
.conclusion-summary :deep(li) {
  margin-bottom: 0.5em;
}
.conclusion-summary :deep(code) {
  background-color: #f0f0f0;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
}
</style>
