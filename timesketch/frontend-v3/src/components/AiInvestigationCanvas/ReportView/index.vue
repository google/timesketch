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
            @click="setShowConfirmationModal()"
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
        <p class="font-italic report-auto-timestamp">
          It will be automatically recorded upon completion.
        </p>
      </div>
      <div class="report-form-group ga-6 mb-12 w-75" v-if="questionsTotal">
        <p class="font-weight-bold">Progress</p>
        <p>
          {{ completedQuestionsTotal }} / {{ questionsTotal }} questions
          finalized
        </p>
      </div>
      <div>
        <div class="d-flex justify-space-between">
          <label for="summary" class="text-h6 font-weight-bold mb-2 d-block"
            >Summary</label
          >
          <!-- <v-btn
              variant="text"
              size="small"
              color="primary"
              @click="reqenerateSummary()"
              :disabled="reportLocked"
              class="text-uppercase"
            >
              <v-icon icon="mdi-reload" class="mr-2" left small />
              Regenerate Summary (TODO)</v-btn
            > -->
          <v-btn
            variant="text"
            size="small"
            color="primary"
            @click="setShowSummaryHistoryModal()"
            class="text-uppercase"
          >
            <v-icon icon="mdi-open-in-new" class="mr-2" left small />
            View History</v-btn
          >
        </div>
        <div class="position-relative">
          <div
            v-if="isSavingSummary"
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
            :disabled="reportLocked"
            rows="5"
            noResize
            hide-details
            class="mb-2"
          ></v-textarea>
        </div>
        <div class="d-flex justify-space-between">
          <v-btn
            variant="text"
            size="small"
            color="primary"
            @click="submitSummary()"
            :disabled="isSavingSummary || reportLocked"
            class="text-uppercase"
          >
            <v-icon icon="mdi-tray-arrow-up" class="mr-2" left small />
            Save</v-btn
          >

          <time class="font-italic text-body-2">
            Last updated
            {{ formatDate(store.report.content.summary[0].timestamp) }}
          </time>
        </div>
      </div>
    </form>

    <div class="px-6" v-if="questionsTotal">
      <h3 class="text-h6 font-weight-bold mb-5">Key Findings</h3>
      <ol class="questions-list">
        <KeyFindingItem
          v-for="(question, index) in questions"
          :question="question"
          :index="index"
          :key="question.id"
          :reportLocked="reportLocked"
        />
      </ol>
    </div>
  </section>
  <v-dialog
    transition="dialog-bottom-transition"
    v-model="showConfirmationModal"
    width="auto"
  >
    <CompleteInvestigationModal
      @close-modal="setShowConfirmationModal"
      :questions="questions"
    />
  </v-dialog>
  <v-dialog
    transition="dialog-bottom-transition"
    v-model="showSummaryHistoryModal"
    width="865px"
    max-height="420px"
    opacity="0"
  >
    <SummaryHistoryModal
      @close-modal="setShowSummaryHistoryModal"
      :summaries="store.report.content.summary"
    />
  </v-dialog>
</template>

<script>
import { useAppStore } from "@/stores/app";
import dayjs from "dayjs";
import { debounce } from "lodash";
import SummaryHistoryModal from "../Modals/SummaryHistoryModal.vue";
import { formatDate } from "@/utils/TimeDate";

export default {
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
      showSummaryHistoryModal: false,
      isSavingSummary: false,
      summary: store.report?.content?.summary?.[0].value,
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
  },
  methods: {
    formatDate,
    setShowConfirmationModal() {
      this.showConfirmationModal = !this.showConfirmationModal;
    },
    setShowSummaryHistoryModal() {
      this.showSummaryHistoryModal = !this.showSummaryHistoryModal;
    },
    async unlockReport() {
      try {
        await this.store.updateReport({ verified: false });

        this.store.setNotification({
          text: `Report Unlocked`,
          icon: "mdi-lock-open-variant-outline",
          type: "success",
        });
      } catch (error) {
        console.error(error);
        this.store.setNotification({
          text: "Unable to unlock this report. Please try again.",
          icon: "mdi-alert-circle-outline",
          type: "error",
        });
      } finally {
      }
    },
    downloadReport() {},
    async submitSummary() {
      try {
        this.isSavingSummary = true;

        await this.store.updateReport({
          summary: [
            { timestamp: dayjs(), value: this.summary },
            ...this.store.report.content.summary,
          ],
        });
      } catch (error) {
        console.error(error);
      } finally {
        this.isSavingSummary = false;
      }
    },
    updateContent: debounce(function (key, value) {
      this.store.updateReport({ [key]: value });
    }, 200),
  },
  watch: {
    riskLevel(riskLevel) {
      this.riskLevel = riskLevel;
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

.summary-loader {
  z-index: 1;
  background: rgba(255, 255, 255, 0.75);
}
</style>
