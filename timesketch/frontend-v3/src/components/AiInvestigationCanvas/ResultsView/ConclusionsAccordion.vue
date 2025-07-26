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
  <div class="px-6">
    <div class="d-flex justify-space-between">
      <h3 class="text-h6 font-weight-bold mb-3">Conclusions</h3>
       <!-- Add New Conclusion Modal -->
      <v-btn
        variant="text"
        size="small"
        color="primary"
        @click="openEditModal(false)"
        :disabled="hasCurrentUserConclusion || isQuestionVerified || isQuestionRejected"
      >
        Add Your Conclusion
      </v-btn>
    </div>

    <v-expansion-panels class="mb-6" v-model="panels">
      <v-expansion-panel
        color="#F8F9FA"
        v-if="hasConclusions"
        v-for="conclusion in question.conclusions"
        :value="conclusion.id"
        :key="conclusion.id"
      >
        <v-expansion-panel-title color="#F8F9FA">
          <div class="d-flex align-center justify-space-between w-100">
            <div>
              <p>
                {{ conclusion.conclusion }}
              </p>
              <v-spacer />
              <v-chip v-if="conclusion.automated"
                size="x-small"
                variant="outlined"
                class="px-2 py-2 rounded-l mt-2"
                color="#5F6368"
              >
                Pre-Detected by AI
              </v-chip>
            </div>
            <v-btn
                v-if="isEditable(conclusion)"
                icon="mdi-pencil"
                variant="text"
                size="small"
                class="ml-4 flex-shrink-0"
                @click.stop="openEditModal(conclusion)"
            />
          </div>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <ObservableEvents
            :events="conclusion.conclusion_events"
            :conclusionId="conclusion.id"
          />
          <v-btn
            v-if="!conclusion.automated"
            size="small"
            variant="text"
            depressed
            @click="openEventLog()"
            :disabled="!isQuestionVerified && isQuestionRejected"
            color="primary"
          >
            <v-icon left small icon="mdi-plus" />
            Add more events
          </v-btn>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
  <!-- Edit Conclusion Modal -->
  <v-dialog
    transition="dialog-bottom-transition"
    v-model="showEditModal"
    width="auto"
  >
    <EditConclusionModal
      v-if="editingConclusion"
      headline="Edit Your Conclusion"
      :conclusion="editingConclusion"
      :question="question"
      @close-modal="handleModalClose"
    />
    <EditConclusionModal
      v-else
      headline="Add Your Conclusion"
      :conclusion="{}"
      :question="question"
      @close-modal="handleModalClose"
    />
  </v-dialog>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  props: {
    question: Object,
  },
  inject: ["updateQuestion", "confirmRemoveQuestion", "refreshQuestionById"],
  data() {
    return {
      store: useAppStore(),
      showModal: false,
      showEventLog: false,
      isConfirming: false,
      showEditModal: false,
      editingConclusion: null,
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
        this.question?.status?.status === 'verified'
      )
    },
    isQuestionRejected() {
      return this.question?.status?.status === 'rejected'
    },
    hasCurrentUserConclusion() {
      return this.question?.conclusions?.some(
        (conclusion) => conclusion.user.name === this.store.currentUser
      );
    },
  },
  methods: {
    openEventLog() {
      this.showEventLog = true;
    },
    closeEventLog() {
      this.showEventLog = false;
    },
    isEditable(conclusion) {
      // Not automated, not locked and owned by the current user
      return !conclusion.automated &&
             !this.store.reportLocked &&
             conclusion.user.username === this.store.currentUser;
    },
    openEditModal(conclusion) {
      this.editingConclusion = conclusion;
      this.showEditModal = true;
    },
    handleModalClose() {
      this.showEditModal = false
      this.editingConclusion = null
      if (this.question?.id) {
        this.refreshQuestionById(this.question.id)
      }
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
