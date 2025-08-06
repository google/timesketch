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
  <v-container fluid class="modal pa-5 rounded-lg">
    <ModalLoader :isSubmitting="isSubmitting" />
    <div :class="modalClasses">
      <div>
        <h3 class="mb-4">Are you sure?</h3>
      </div>
      <p class="mb-10">
        You will not be able to recover this question, and its related data if
        you decide to remove it from this report
      </p>
      <div class="d-flex justify-end align-center ga-4">
        <v-btn
          variant="text"
          size="small"
          color="primary"
          @click="$emit('close-modal')"
        >
          <v-icon class="mr-1" left small />
          No, keep question</v-btn
        >
        <v-btn color="primary" @click="deleteQuestion()">
          Yes, question is not relevant</v-btn
        >
      </div>
    </div>
  </v-container>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  props: {
    questionId: Number,
  },
  data() {
    return {
      store: useAppStore(),
      isSubmitting: false,
    };
  },
  methods: {
    async deleteQuestion() {
      try {
        this.isSubmitting = true;

        const existingRemovedQuestions =
          this.store.report?.content?.removedQuestions || [];

        const filteredApprovedQuestions = this.store.report?.content
          ?.approvedQuestions
          ? this.store.report?.content?.approvedQuestions.filter(
              (id) => id !== this.questionId
            )
          : [];

        await this.store.updateReport({
          approvedQuestions: filteredApprovedQuestions,
          removedQuestions: [...existingRemovedQuestions, this.questionId],
        });

        this.$emit("close-modal");

        this.store.setActiveQuestion(null);

        this.store.setNotification({
          text: `You successfully deleted question ${this.questionId}`,
          icon: "mdi-minus-circle-outline",
          type: "success",
        });
      } catch (error) {
        console.error(error);
        this.store.setNotification({
          text: "Unable to delete question. Please try again.",
          icon: "mdi-alert-circle-outline",
          type: "error",
        });
      } finally {
        this.isSubmitting = false;
      }
    },
  },
  computed: {
    modalClasses() {
      return {
        modal__content: true,
        'no-pointer-events': this.isSubmitting
      }
    },
  }
};
</script>

<style scoped>
.modal {
  width: 500px;
  background-color: #fff;
}

.modal__content {
  display: grid;
  grid-template-rows: auto auto auto;
}

.create-question {
  z-index: 3;
  order: 2;
}

.questions-group {
  -ms-overflow-style: none;
  scrollbar-width: none;
  overflow-y: auto;
}

.dfiq-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  border-top: 1px dashed #dadce0;
  font-size: 14px;
}

.no-pointer-events {
  pointer-events: none;
}
</style>
