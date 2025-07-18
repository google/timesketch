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
  <section>
    <header class="report-header px-6 pa-4 mb-6">
      <v-btn
        variant="text"
        class="ai-inline-cta ml-n3"
        :disabled="disableCta"
        @click="store.setActiveQuestion(null)"
      >
        <v-icon size="large" icon="mdi-arrow-left" />
        Report
      </v-btn>
      <QuestionActionsStrip
        v-if="!reportLocked"
        :isApproved="isApproved"
        :question="question"
        variant="default"
      />
      <div class="d-inline-flex ga-2 align-center mb-4">
        <v-icon
          icon="mdi-check-circle"
          v-if="isApproved"
          size="large"
          color="#34A853"
        />
      </div>

      <h1 class="mb-4 text-h4 font-weight-bold">
        {{ question.name }}
      </h1>
    </header>

    <div class="px-6 mb-8">
      <ConclusionSummary :question="question" />
    </div>
    <ConclusionsAccordion :question="question" />
  </section>
</template>

<script>
import { useAppStore } from "@/stores/app";
import ConclusionSummary from "./ConclusionSummary.vue";

export default {
  props: {
    question: Object,
    reportLocked: Boolean,
    isLoading: Boolean,
  },
  inject: ["updateQuestion", "confirmRemoveQuestion"],
  data() {
    return {
      store: useAppStore(),
      panels:
        this.question.conclusions && this.question.conclusions.length
          ? [this.question.conclusions[0].id]
          : ["fallback"],
    };
  },
  computed: {
    disableCta() {
      return !this.store.activeContext.question?.id;
    },
    isApproved() {
      return !!this.store.report?.content?.approvedQuestions?.find(
        (approvedId) => approvedId === this.question.id
      );
    },
  },
};
</script>

<style>
.questions-list {
  list-style: none;
}

.question::marker {
  font-size: inherit;
  font-weight: inherit;
}
</style>
