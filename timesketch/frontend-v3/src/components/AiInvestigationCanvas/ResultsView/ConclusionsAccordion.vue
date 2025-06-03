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
  <div class="px-6">
    <div class="d-flex justify-space-between">
      <h3 class="text-h6 font-weight-bold mb-3">Key Observables</h3>
      <v-chip
        size="x-small"
        variant="outlined"
        class="px-2 py-2 rounded-l"
        color="#5F6368"
        v-if="!question?.user"
      >
        Pre-Detected by AI
      </v-chip>
    </div>

    <v-expansion-panels class="mb-6" v-model="panels">
      <v-expansion-panel
        color="#F8F9FA"
        v-if="hasConclusions"
        v-for="conclusion in question.conclusions"
        :value="conclusion.id"
      >
        <v-expansion-panel-title color="#F8F9FA">
          <div>
            <p>
              {{ conclusion.conclusion }}
            </p>
          </div>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <ObservableEvents
            :events="conclusion.conclusion_events"
            :conclusionId="conclusion.id"
          />
          <v-btn
            size="small"
            variant="text"
            depressed
            @click="openEventLog()"
            :disabled="isQuestionVerified"
            color="primary"
          >
            <v-icon left small icon="mdi-plus" />
            Add more facts
          </v-btn>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  props: {
    question: Object,
  },
  inject: ["updateQuestion", "confirmRemoveQuestion"],
  data() {
    return {
      store: useAppStore(),
      showModal: false,
      showEventLog: false,
      isConfirming: false,
      panels:
        this.question?.conclusions && this.question.conclusions.length > 0
          ? [this.question.conclusions[0].id]
          : ["fallback"],
    };
  },
  computed: {
    hasConclusions() {
      return this.question?.conclusions && this.question.conclusions.length > 0;
    },
    isQuestionVerified() {
      return (
        this.store.reportLocked ||
        this.store.approvedReportQuestions.includes(this.question.id)
      )
    },
  },
  methods: {
    openEventLog() {
      this.showEventLog = true;
    },
    closeEventLog() {
      this.showEventLog = false;
    },
  },
  provide() {
    return {
      showEventLog: computed(() => this.showEventLog),
      closeEventLog: this.closeEventLog,
    };
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
