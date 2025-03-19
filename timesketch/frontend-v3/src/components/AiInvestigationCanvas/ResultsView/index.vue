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
    <header class="report-header px-6 pa-4">
      <h2 class="text-h5 font-weight-bold mb-6">Results</h2>
      <QuestionActionsStrip
        v-if="!reportLocked"
        :completed="completed"
        :question="question"
        variant="b"
      />
      <div class="d-inline-flex ga-2 align-center mb-4">
        <RiskLevelControl
          :riskLevel="riskLevel"
          :disabled="reportLocked"
          @update:riskLevel="($event) => (riskLevel = $event)"
        />
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
      <div class="d-flex justify-space-between">
        <label for="conclusion" class="text-h6 font-weight-bold d-block mb-2"
          >Conclusion</label
        >
        <v-chip
          v-if="!question.user"
          size="x-small"
          variant="outlined"
          class="px-2 py-2 rounded-l"
          color="#5F6368"
        >
          Pre-Suggested by AI
        </v-chip>
      </div>
      <v-textarea
        :disabled="reportLocked"
        v-model="conclusion"
        hide-details="auto"
        id="conclusion"
        name="conclusion"
        variant="outlined"
        class="mb-2"
        rows="3"
      ></v-textarea>
      <div>
        <v-btn
          :disabled="reportLocked"
          variant="text"
          size="small"
          color="primary"
          class="text-uppercase pa-0"
          @click="regenerateConclusion()"
        >
          <v-icon icon="mdi-reload" left small class="mr-1" />
          Regenerate Conclusion (TODO)</v-btn
        >
        <v-btn
          variant="text"
          size="small"
          color="primary"
          @click="showRevisionHistory()"
          :disabled="reportLocked"
          class="text-uppercase ml-5"
        >
          <v-icon icon="mdi-invoice-list-outline" class="mr-2" left small />
          View History (TODO)</v-btn
        >
      </div>
    </div>
    <div class="px-6">
      <div class="d-flex justify-space-between">
        <h3 class="text-h6 font-weight-bold mb-3">Key Observables</h3>
        <v-chip
          size="x-small"
          variant="outlined"
          class="px-2 py-2 rounded-l"
          color="#5F6368"
          v-if="!question.user"
        >
          Pre-Detected by AI
        </v-chip>
      </div>

      <v-expansion-panels class="mb-6">
        <v-expansion-panel
          color="#F8F9FA"
          v-if="question.observables"
          v-for="observable in question.observables"
        >
          <v-expansion-panel-title color="#F8F9FA">
            <div>
              <h5 class="h4 font-weight-bold mb-2">
                {{ observable.observable_type }}
              </h5>
              <p>
                {{ observable.conclusion }}
              </p>
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <ObservableEvents :events="observable.entities" :details="observable.log_details" />
            <v-btn
              size="small"
              variant="text"
              depressed
              @click="openEventLog()"
              color="primary"
            >
              <v-icon left small icon="mdi-plus" />
              Add more facts
            </v-btn>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <v-expansion-panel color="#F8F9FA" v-else>
          <v-expansion-panel-title color="#F8F9FA">
            <div>
              <h5 class="h4 font-weight-bold mb-2">Dave's observable</h5>
              <p>
                {{ conclusion }}
              </p>
            </div>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-btn
              size="small"
              variant="text"
              depressed
              @click="openEventLog()"
              color="primary"
            >
              <v-icon left small icon="mdi-plus" />
              Add more facts
            </v-btn>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </div>
  </section>
</template>

<script>
import { useAppStore } from "@/stores/app";
import RestApiClient from "@/utils/RestApiClient";
import { debounce } from "lodash";

export default {
  props: {
    question: Object,
    reportLocked: Boolean,
  },
  inject: ["updateQuestion", "confirmRemoveQuestion", "openEventLog"],
  data() {
    return {
      store: useAppStore(),
      showModal: false,
      showEventList: false,
      isConfirming: false,
      riskLevel: this.question.riskLevel,
      conclusion: this.question.conclusion,
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
    async regenerateConclusion() {
      // TODO : Implement when API work is completed
    },
    async toggleEventList() {
      this.showEventList = !this.showEventList;
    },
  },
  watch: {
    conclusion: debounce(async function (conclusion) {
      const response = await RestApiClient.createQuestionConclusion(
        this.store.sketch.id,
        this.question.id,
        conclusion
      );

      this.updateQuestion({
        ...response.data.objects[0],
        conclusion:
          response.data.objects[0].conclusions?.length > 0
            ? response.data.objects[0].conclusions
                .map(({ conclusion }) => conclusion)
                .join()
            : "",
      });
    }, 200),
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
