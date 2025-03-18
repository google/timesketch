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
      <v-card
        :color="completed || reportLocked ? '#F8F9FA' : '#3874CB'"
        class="mb-14 d-flex align-center justify-space-between pa-2"
        flat
      >
        <v-card-item>
          <p class="font-weight-medium mb-1">
            Would you like to save the results to the report?
          </p>
        </v-card-item>

        <v-card-actions>
          <v-btn
            :disabled="reportLocked"
            @click="confirmRemoveQuestion(question.id)"
            :color="completed ? 'primary' : '#fff'"
            size="small"
            >Remove Question</v-btn
          >
          <v-btn
            :disabled="isConfirming || completed || reportLocked"
            rounded
            variant="flat"
            :color="isConfirming || completed || reportLocked ? 'primary' : '#fff'"
            size="small"
            @click="confirmAndSave()"
            >{{
              isConfirming
                ? "Saving"
                : completed
                ? "Saved"
                : "Confirm &amp; Save"
            }}
            <v-progress-circular
              v-if="isConfirming"
              :size="20"
              :width="2"
              color="#fff"
              indeterminate
              class="ml-2"
            />
          </v-btn>
        </v-card-actions>
      </v-card>
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
    </div>
    <div class="px-6">
      <div class="d-flex justify-space-between">
        <h3 class="text-h6 font-weight-bold mb-3">Key Observables</h3>
        <v-chip
          size="x-small"
          variant="outlined"
          class="px-2 py-2 rounded-l"
          color="#5F6368"
        >
          Pre-Detected by AI
        </v-chip>
      </div>

      <v-expansion-panels class="mb-6">
        <v-expansion-panel
          color="#F8F9FA"
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
            <!-- <EventsList :query-request="activeQueryRequest"></EventsList> -->
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </div>
  </section>
</template>

<script setup>
import RestApiClient from "@/utils/RestApiClient";
// import EventsList from "../EventsList.vue";
import { useAppStore } from "@/stores/app";
import { watch } from "vue";
import { debounce } from "lodash";

const store = useAppStore();

const { question, reportLocked } = defineProps({
  question: Object,
  reportLocked: Boolean
});

const completed = computed(() => {
  let isApproved = false;

  if (store.report?.content?.approvedQuestions && store.report?.content?.approvedQuestions.length > 0) {
    isApproved = !!store.report.content.approvedQuestions.find(
      (approvedId) => approvedId === question.id
    );
  }

  return isApproved;
});

const isConfirming = ref(false);
const riskLevel = ref(question.riskLevel);
const conclusion = ref(question.conclusion);

async function regenerateConclusion() {}

watch(
  conclusion,
  debounce(async (conclusion) => {
    const response = await RestApiClient.createQuestionConclusion(
      store.sketch.id,
      question.id,
      conclusion
    );

    updateQuestion({
      ...response.data.objects[0],
      conclusion:
        response.data.objects[0].conclusions?.length > 0
          ? response.data.objects[0].conclusions
              .map(({ conclusion }) => conclusion)
              .join()
          : "",
    });
  }, 500)
);

const updateQuestion = inject("updateQuestion");

watch(riskLevel, (riskLevel) => {
  updateQuestion({ ...question, riskLevel });
  store.setActiveQuestion({ ...question, riskLevel });
});

const confirmRemoveQuestion = inject("confirmRemoveQuestion");

async function confirmAndSave() {
  isConfirming.value = true;

  try {
    const existingQuestions = store.report?.content?.approvedQuestions || [];

    await store.updateReport({
      approvedQuestions: new Set([...existingQuestions, question.id]),
    });

    store.setNotification({
      text: `Question approved`,
      icon: "mdi-check-circle-outline",
      type: "success",
    });
  } catch (error) {
    store.setNotification({
      text: `Unable to approve question`,
      icon: "mdi-close-circle-outline",
      type: "error",
    });
  } finally {
    isConfirming.value = false;
  }
}
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
