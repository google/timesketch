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
  <v-container fluid class="modal pa-8 rounded-lg">
    <ModalLoader :isSubmitting="isSubmitting" />
    <div :class="{ modal__content: true, 'no-pointer-events': isSubmitting }">
      <div>
        <h3 class="mb-4">Want to complete the investigation?</h3>
        <p class="mb-4">
          These unsaved questions and results will remain, but progress will
          still be marked as 100% complete. Are you sure you want to continue?
        </p>
        <p class="mb4 font-weight-medium">Unsaved questions:</p>
      </div>

      <div class="questions-list overflow-hidden overflow-y-auto">
        <ul>
          <li v-for="question in unsavedQuestions">{{ question.name }}</li>
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
        <v-btn rounded color="primary" @click="fileReport()">
          Complete investigation</v-btn
        >
      </div>
    </div>
  </v-container>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  props: {
    questions: Array
  },
  data() {
    return {
      store: useAppStore(),
      isSubmitting: false,
    };
  },
  methods: {
    async fileReport() {
      this.isSubmitting = true;

      try {
        await this.store.updateReport({ verified: true });

        this.$emit("close-modal");

        this.store.setNotification({
          text: `Report Filed`,
          icon: "mdi-file-check-outline",
          type: "success",
        });
      } catch (error) {
        console.error(error);

        this.store.setNotification({
          text: "Unable to file this report. Please try again.",
          icon: "mdi-alert-circle-outline",
          type: "error",
        });
      } finally {
        this.isSubmitting = false;
      }
    },
  },
  computed: {
    unsavedQuestions() {
      return this.questions.filter(
        ({ id }) => !this.store.report.content.approvedQuestions.includes(id)
      );
    },
  },
};
</script>

<style scoped>
.modal {
  width: 600px;
  height: 450px;
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
