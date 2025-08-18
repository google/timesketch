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
  <v-container fluid class="modal pa-8 rounded-lg">
    <ModalLoader :isSubmitting="isSubmitting" />
    <div :class="modalClasses">
      <div>
        <h3 class="mb-4">
          <v-icon class="mr-2" icon="mdi-alert-circle-outline" color="warning"/>
          Finalize Investigation
        </h3>
        <p class="mb-4">
          You have questions that are not yet answered (verified) or marked as not relevant (rejected).
          <br />
          To complete the investigation, the following unanswered questions will be marked as 'not relevant' (rejected).
          <br />
          <br />
          Are you sure you want to continue?
        </p>
        <p class="mb-2 font-weight-medium">Questions to be rejected:</p>
      </div>

      <div class="questions-list overflow-hidden overflow-y-auto">
        <ul>
          <li v-for="question in unsavedQuestions" :key="question.id">* {{ question.name }}</li>
        </ul>
      </div>
      <div class="d-flex align-center justify-end ga-4 pa-4">
        <v-btn
          variant="text"
          size="small"
          color="primary"
          @click="$emit('close-modal')"
        >
          <v-icon class="mr-1" left small />
          Cancel</v-btn
        >
        <v-btn color="primary" @click="rejectAndComplete()">
          Reject and Complete
        </v-btn>
      </div>
    </div>
  </v-container>
</template>

<script>
import { ReportStatus, useAppStore } from "@/stores/app";
import dayjs from "dayjs";
import RestApiClient from "@/utils/RestApiClient";

export default {
  props: {
    questions: Array,
    unsavedQuestions: Array,
  },
  data() {
    return {
      store: useAppStore(),
      isSubmitting: false,
    };
  },
  methods: {
    async rejectAndComplete() {
      this.isSubmitting = true

      try {
        const unsavedIds = this.unsavedQuestions.map((q) => q.id)

        // Update status for all unsaved questions to 'rejected'
        const updatePromises = unsavedIds.map((id) =>
          RestApiClient.updateQuestion(this.store.sketch.id, id, { status: 'rejected' })
        )
        await Promise.all(updatePromises)

        // Now, complete the report
        await this.store.updateReport({
          status: ReportStatus.VERIFIED,
          completedDateTime: dayjs(),
        });

        this.$emit('completed')
        this.$emit("close-modal")

        this.store.setNotification({
          text: 'Unsaved questions rejected and report locked.',
          icon: "mdi-file-check-outline",
          type: "success",
        });
      } catch (error) {
        console.error(error)

        this.store.setNotification({
          text: "Unable to lock this report. Please try again.",
          icon: "mdi-alert-circle-outline",
          type: "error",
        });
      } finally {
        this.isSubmitting = false
      }
    },
  },
  computed: {
    modalClasses() {
      return {
        modal__content: true,
        'no-pointer-events': this.isSubmitting,
      }
    },
  },
};
</script>

<style scoped>
.modal {
  width: 600px;
  background-color: #fff;
}

.modal__content {
  display: grid;
  grid-template-rows: auto 200px auto;
  -ms-overflow-style: none;
  scrollbar-width: none;
  overflow-y: auto;
}
.create-question {
  z-index: 3;
  order: 2;
}

.questions-list {
  -ms-overflow-style: none;
  scrollbar-width: none;
  overflow-y: auto;
}
</style>
