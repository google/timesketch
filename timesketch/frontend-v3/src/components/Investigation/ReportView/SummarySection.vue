<!--
Copyright 2025 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

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
        >Summary</label
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
        hide-details
        class="summary-field mb-2"
      ></v-textarea>
    </div>
    <div class="d-flex justify-space-between align-center">
      <v-btn
        variant="text"
        size="small"
        color="primary"
        @click="submitSummary()"
        :disabled="cannotUpdateSummary"
        class="text-uppercase"
      >
        <v-icon icon="mdi-tray-arrow-up" class="mr-2" left small />
        Save</v-btn
      >

      <time class="font-italic text-body-2" v-if="lastUpdated">
        Last updated {{ lastUpdated }}
      </time>
    </div>
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

export default {
  props: {
    reportLocked: Boolean,
  },
  data() {
    const store = useAppStore();

    return {
      store,
      showSummaryHistoryModal: false,
      isSavingSummary: false,
      summary: store.report?.content?.summary?.[0].value,
    };
  },
  computed: {
    summaries() {
      return this.store.report?.content?.summary
    },
    latestSummary() {
      return this.store.report?.content?.summary?.[0];
    },
    lastUpdated() {
      if (!this.latestSummary) {
        return null;
      }

      const timestamp = formatDate(this.latestSummary.timestamp)
      const user =  this.latestSummary.user;

      return `${timestamp}${user ? ` by${user}`: null}`;
    },
    cannotUpdateSummary() {
      const savedSummary = this.latestSummary?.value;

      return (
        this.isSavingSummary ||
        this.reportLocked ||
        savedSummary === this.summary
      );
    },
  },
  methods: {
    formatDate,
    toggleShowSummaryHistoryModal() {
      this.showSummaryHistoryModal = !this.showSummaryHistoryModal;
    },
    async submitSummary() {
      try {
        this.isSavingSummary = true;

        await this.store.updateReport({
          summary: [
            {
              timestamp: dayjs(),
              value: this.summary,
              user: this.store.currentUser,
            },
            ...(this.store.report.content.summary ?? []),
          ],
        });

        this.store.setNotification({
          text: "Summary saved",
          icon: "mdi-content-save-edit-outline",
          type: "success",
        });
      } catch (error) {
        console.error(error);

        this.store.setNotification({
          text: "Unable to save summary",
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
.summary-loader {
  z-index: 1;
  background: rgba(255, 255, 255, 0.75);
}

.summary-field__actions {
  bottom: 10px;
}
</style>
