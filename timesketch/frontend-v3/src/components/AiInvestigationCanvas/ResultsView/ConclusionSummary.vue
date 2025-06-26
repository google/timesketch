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
  <div>
    <div class="d-flex justify-space-between">
      <label for="summary" class="text-h6 font-weight-bold mb-2 d-block"
        >Answer</label
      >
      <v-btn
        variant="text"
        size="small"
        color="primary"
        @click="toggleShowSummaryHistoryModal()"
        class="text-uppercase"
        :disabled="!summaries || summaries.length < 1"
      >
        <v-icon icon="mdi-open-in-new" class="mr-2" left small />
        View History</v-btn
      >
    </div>

    <form @submit.prevent="submitSummary()">
      <div class="position-relative">
        <div
          v-if="isSavingSummary || isSynthesizing"
          class="summary-loader position-absolute top-0 left-0 d-flex align-center justify-center w-100 fill-height"
        >
          <v-progress-circular
            indeterminate
            size="60"
            width="3"
            color="primary"
          ></v-progress-circular>
        </div>
        <v-textarea
          v-model="summary"
          id="summary"
          name="summary"
          variant="outlined"
          :disabled="isTextareaDisabled"
          rows="3"
          hide-details
          class="mb-2"
        ></v-textarea>
      </div>
      <div class="d-flex justify-space-between align-center">
        <div>
          <v-btn
            variant="text"
            size="small"
            color="primary"
            type="submit"
            :disabled="cannotUpdateSummary"
            class="text-uppercase"
            title="Save your answer for this question."
          >
            <v-icon icon="mdi-tray-arrow-up" class="mr-2" left small />
            Save</v-btn
          >
          <v-btn
            v-if="isSynthesizeAvailable"
            variant="text"
            size="small"
            color="primary"
            @click="handleSynthesizeClick"
            :loading="isSynthesizing"
            :disabled="isTextareaDisabled"
            class="text-uppercase ml-2"
            title="Generate a new answer using AI based on the latest conclusions."
          >
            <v-icon icon="mdi-creation" class="mr-2" left small />
            Summarize Conclusions
          </v-btn>
        </div>

        <time class="font-italic text-body-2" v-if="lastUpdated">
          Last updated {{ lastUpdated }}
        </time>
      </div>
    </form>
  </div>
  <v-dialog
    transition="dialog-bottom-transition"
    v-model="showSummaryHistoryModal"
    width="865px"
    max-height="420px"
    opacity="0"
  >
    <SummaryHistoryModal
      @close-modal="toggleShowSummaryHistoryModal"
      :summaries="summaries"
    />
  </v-dialog>
</template>

<script>
import { useAppStore } from "@/stores/app";
import dayjs from "dayjs";
import SummaryHistoryModal from "../Modals/SummaryHistoryModal.vue";
import { formatDate } from "@/utils/TimeDate";
import RestApiClient from "@/utils/RestApiClient";

export default {
  props: {
    reportLocked: Boolean,
    question: Object,
  },
  data() {
    return {
      store: useAppStore(),
      showSummaryHistoryModal: false,
      isSavingSummary: false,
      isSynthesizing: false,
      summary: "",
    };
  },
  mounted() {
    if (!this.summaries || this.summaries.length < 1) {
      if (this.isSynthesizeAvailable) {
        this.fetchSynthesizedAnswer();
      } else {
        this.summary = "<Please add or review the conclusions and provide your answer to the question here>";
      }
    } else {
      this.summary = this.summaries?.[0]?.value;
    }
  },
  computed: {
    isSynthesizeAvailable() {
      if (
        this.store.systemSettings.LLM_FEATURES_AVAILABLE?.llm_synthesize === true ||
        this.store.systemSettings.LLM_FEATURES_AVAILABLE?.default === true
      ){
        return true
      }
      return false
    },
    summaries() {
      return (
        this.store.report?.content?.conclusionSummaries?.filter(
          ({ questionId }) => questionId === this.question.id
        ) ?? []
      );
    },
    latestSummary() {
      return this.summaries[0];
    },
    lastUpdated() {
      if (!this.latestSummary) {
        return null;
      }

      return `${formatDate(this.latestSummary.timestamp)}${
        this.latestSummary.user ? ` by
      ${this.latestSummary.user}` : null
      }`;
    },
    cannotUpdateSummary() {
      const savedSummary = this.summaries?.[0]?.value || "";

      return (
        this.isSavingSummary ||
        this.isSynthesizing ||
        this.reportLocked ||
        !this.summary ||
        savedSummary === this.summary
      );
    },
    isTextareaDisabled() {
      return (
        this.reportLocked ||
        this.store.approvedReportQuestions.includes(this.question.id) ||
        this.isSynthesizing
      );
    },
  },
  methods: {
    formatDate,
    toggleShowSummaryHistoryModal() {
      this.showSummaryHistoryModal = !this.showSummaryHistoryModal;
    },
    async handleSynthesizeClick() {
      await this.fetchSynthesizedAnswer();
    },
    async fetchSynthesizedAnswer() {
      this.isSynthesizing = true;
      try {
        const response = await RestApiClient.llmRequest(
          this.store.sketch.id,
          "llm_synthesize",
          { question_id: this.question.id }
        );
        this.summary = response.data.response;
        await this.submitSummary('<AI>');
      } catch (e) {
        console.error("Error synthesizing answer:", e);
        this.summary =
          "Failed to generate an answer. Please check the conclusions and logs and try again.";
      } finally {
        this.isSynthesizing = false;
      }
    },
    async submitSummary(user) {
      try {
        this.isSavingSummary = true;

        if (!this.question.id) {
          throw new Error("No question ID to work with");
        }

        await this.store.updateReport({
          conclusionSummaries: [
            {
              questionId: this.question.id,
              timestamp: dayjs(),
              value: this.summary,
              user: user ? user : this.store.currentUser,
            },
            ...(this.store.report.content.conclusionSummaries || []),
          ],
        });

        this.store.setNotification({
          text: "Answer saved",
          icon: "mdi-content-save-edit-outline",
          type: "success",
        });
      } catch (error) {
        console.error(error);

        this.store.setNotification({
          text: "Unable to save Answer",
          icon: "mdi-lock-open-variant-outline",
          type: "error",
        });
      } finally {
        this.isSavingSummary = false;
      }
    },
  },
};
</script>

<style>
.conclusion-summary-loader {
  z-index: 1;
  background: rgba(255, 255, 255, 0.75);
}

.conclusion-summary-field__actions {
  bottom: 10px;
}
</style>
