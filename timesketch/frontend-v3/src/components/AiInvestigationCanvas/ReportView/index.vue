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
    <!-- NEW: Empty state when no questions exist -->
    <div v-if="!isLoading && questionsTotal === 0" class="px-6 py-16 text-center">
      <v-icon size="80" color="disabled" class="mb-4">mdi-text-box-search-outline</v-icon>
      <h2 class="text-h4 font-weight-bold mb-4">Start Your AI-Powered Investigation</h2>
      <p class="mb-8 mx-auto" style="max-width: 600px;">
        There are currently no investigative questions in this report.
        Click the button below to have Timesketch AI analyze all timeline data in this sketch.
        It will automatically generate key findings and investigative questions to kickstart your analysis.
      </p>
      <v-btn
        size="large"
        rounded
        color="primary"
        @click="runLogAnalysis()"
        :loading="isGeneratingReport"
        :disabled="isGeneratingReport"
      >
        <v-icon left>mdi-creation</v-icon>
        {{ isGeneratingReport ? 'Generating Report...' : 'Generate Initial Report' }}
      </v-btn>
    </div>
    <!-- Existing view for when questions are present -->
    <div v-else>
      <header class="report-header px-6 pt-8 pb-8 mb-8 border-b-thin">
        <h2 class="mb-4 text-h3 font-weight-bold">Investigation Report</h2>
        <div class="d-flex align-center justify-space-between">
          <v-chip
            size="x-small"
            variant="outlined"
            class="px-2 py-2 rounded-l"
            color="#5F6368"
          >
            Pre-generated Report by AI
          </v-chip>
          <div class="d-flex align-center ga-4">
            <v-btn
              v-if="reportLocked"
              variant="text"
              size="small"
              color="primary"
              @click="unlockReport()"
            >
              <v-icon icon="mdi-file-edit-outline" class="mr-1" left small />
              Edit</v-btn
            >
            <v-btn
              variant="text"
              size="small"
              color="primary"
              @click="downloadReport()"
              v-if="reportLocked"
            >
              <v-icon
                icon="mdi-download-circle-outline"
                class="mr-1"
                left
                small
              />
              Download</v-btn
            >
            <v-btn
              v-if="!reportLocked"
              rounded
              color="primary"
              @click="toggleShowConfirmationModal()"
            >
              Complete investigation</v-btn
            >
          </div>
        </div>
      </header>
      <form class="px-6 mb-12">
        <div class="report-form-group mb-6 w-75">
          <label for="name" class="font-weight-bold">Name</label>
          <v-text-field
            hide-details="auto"
            id="name"
            name="name"
            v-model="name"
            variant="outlined"
            density="compact"
            :disabled="reportLocked"
          ></v-text-field>
          <label for="analysts" class="font-weight-bold">Analyst(s)</label>
          <v-text-field
            hide-details="auto"
            id="analysts"
            name="analysts"
            variant="outlined"
            density="compact"
            v-model="analysts"
            :disabled="reportLocked"
          ></v-text-field>
        </div>
        <div class="report-form-group ga-6 mb-6 w-75">
          <p class="font-weight-bold">Finalized Date & Time</p>
          <p class="font-italic report-auto-timestamp">{{ finalizedTime }}</p>
        </div>
        <div class="report-form-group ga-6 mb-12 w-75" v-if="questionsTotal">
          <p class="font-weight-bold">Progress</p>
          <p>
            {{ completedQuestionsTotal }} / {{ questionsTotal }} questions
            finalized
          </p>
        </div>
        <SummarySection :reportLocked="reportLocked" />
      </form>
      <div class="px-6" v-if="questionsTotal">
        <h3 class="text-h6 font-weight-bold mb-5">Key Findings</h3>
        <ol class="questions-list">
          <KeyFindingItem
            v-for="(question, index) in sortedQuestions"
            :question="question"
            :index="index"
            :key="question.id"
            :reportLocked="reportLocked"
          />
        </ol>
      </div>
    </div>
  </section>
  <v-dialog
    transition="dialog-bottom-transition"
    v-model="showConfirmationModal"
    width="auto"
  >
    <CompleteInvestigationModal
      @close-modal="toggleShowConfirmationModal"
      :questions="questions"
    />
  </v-dialog>
</template>
<script>
import { ReportStatus, useAppStore } from "@/stores/app";
import { debounce } from "lodash";
import SummarySection from "./SummarySection.vue";
import dayjs from "dayjs";
import generatePdf from "../_utils/pdf-generator";
export default {
  inject: ["runLogAnalysis", "isGeneratingReport"],
  props: {
    questions: Array,
    questionsTotal: Number,
    completedQuestionsTotal: Number,
    reportLocked: Boolean,
    isLoading: Boolean,
  },
  data() {
    const store = useAppStore();
    return {
      store,
      showConfirmationModal: false,
    };
  },
  computed: {
    analysts: {
      get: function () {
        return this.store.report?.content?.analysts;
      },
      set: function (value) {
        this.store.report.content.analysts = value;
        this.updateContent("analysts", value);
      },
    },
    name: {
      get: function () {
        return this.store.report?.content?.name;
      },
      set: function (value) {
        this.store.report.content.name = value;
        this.updateContent("name", value);
      },
    },
    summary() {
      return this.store.report.content.summary;
    },
    finalizedTime() {
      return this.store.report?.content?.completedDateTime
        ? dayjs(this.store.report.content.completedDateTime).utc()
        : "It will be automatically recorded upon completion.";
    },
    sortedQuestions() {
      if (!this.questions || this.questions.length === 0) {
        return [];
      }
      return [...this.questions].sort((a, b) => a.id - b.id);
    },
  },
  methods: {
    toggleShowConfirmationModal() {
      this.showConfirmationModal = !this.showConfirmationModal;
    },
    downloadReport() {
      const pdfGeneratpr = new generatePdf({
        analysts: this.analysts,
        name: this.name,
        summary: this.summary,
        finalizedTime: this.finalizedTime,
        questions: this.questions,
        id: this.store.report.id,
        questionsTotal: this.questionsTotal,
        completedQuestionsTotal: this.completedQuestionsTotal,
      });
      pdfGeneratpr.generatePdf()
    },
    async unlockReport() {
      try {
        await this.store.updateReport({
          status: ReportStatus.UNVERIFIED,
          completedDateTime: null,
        });
        this.store.setNotification({
          text: "Report Unlocked",
          icon: "mdi-lock-open-variant-outline",
          type: "info",
        });
      } catch (error) {
        console.error(error);
        this.store.setNotification({
          text: "Unable to unlock this report. Please try again.",
          icon: "mdi-alert-circle-outline",
          type: "error",
        });
      }
    },
    updateContent: debounce(function (key, value) {
      this.store.updateReport({ [key]: value });
    }, 200),
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
</style>
