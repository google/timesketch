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
  <ResultsViewLoader v-if="isLoading" />
  <section v-else>
    <header class="report-header px-6 pa-4 mb-6">
      <h2 class="text-h5 font-weight-bold mb-6">Results</h2>
      <QuestionActionsStrip
        v-if="!reportLocked"
        :completed="completed"
        :question="question"
        variant="b"
      />
      <div class="d-inline-flex ga-2 align-center mb-4">
        <!-- <RiskLevelControl
          :riskLevel="riskLevel"
          :disabled="reportLocked"
          @update:riskLevel="($event) => (riskLevel = $event)"
        /> -->
        <v-icon
          icon="mdi-check-circle"
          v-if="completed"
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
      <!-- <div>
        <v-btn
          :disabled="reportLocked"
          variant="text"
          size="small"
          color="primary"
          class="text-uppercase pa-0"
          @click="regenerateConclusion()"
        >
          <v-icon icon="mdi-reload" left small class="mr-1" />
          Regenerate Conclusion Summary</v-btn
        >
        <v-btn
          variant="text"
          size="small"
          color="primary"
          @click="regenerateConclusionSummary()"
          :disabled="reportLocked"
          class="text-uppercase ml-5"
        >
          <v-icon icon="mdi-invoice-list-outline" class="mr-2" left small />
          View History (TODO)</v-btn
        >
      </div> -->
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
  inject: ["updateQuestion", "confirmRemoveQuestion", "openEventLog"],
  data() {
    return {
      store: useAppStore(),
      riskLevel: this.question.riskLevel,
      panels: this.question.conclusions && this.question.conclusions.length
        ? [this.question.conclusions[0].id]
        : ["fallback"],
    };
  },
  computed: {
    completed() {
      let isApproved = false;

      if (
        this.store.report?.content?.approvedQuestions &&
        this.store.report?.content?.approvedQuestions.length > 0
      ) {
        isApproved = !!this.store.report.content.approvedQuestions.find(
          (approvedId) => approvedId === this.question.id
        );
      }

      return isApproved;
    },
  },
  methods: {
    async regenerateConclusionSummary() {
      // TODO : Implement when API work is completed
    },
  },
  watch: {
    riskLevel(riskLevel) {
      this.updateQuestion({ ...this.question, risk_level: riskLevel });
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
