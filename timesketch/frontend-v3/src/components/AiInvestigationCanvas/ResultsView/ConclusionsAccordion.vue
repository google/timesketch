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
        v-if="hasConclusions"
        variant="text"
        size="small"
        color="primary"
        @click="openEditModal(false)"
        :disabled="hasCurrentUserConclusion || isQuestionVerified || isQuestionRejected"
      >
        Add Your Conclusion
      </v-btn>
    </div>

    <v-expansion-panels v-if="hasConclusions" class="mb-6" v-model="panels">
      <v-expansion-panel
        color="#F8F9FA"
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
                <v-icon icon="mdi-creation" class="mr-2" />Detected by AI
              </v-chip>
            </div>
            <div class="ml-4 mr-2 flex-shrink-0 d-flex align-center">
              <v-btn
                  v-if="isEditable(conclusion)"
                  icon="mdi-pencil"
                  variant="text"
                  size="small"
                  @click.stop="openEditModal(conclusion)"
                  title="Edit conclusion"
              />
              <v-btn
                  v-if="isDeletable(conclusion)"
                  icon="mdi-delete-outline"
                  variant="text"
                  size="small"
                  @click.stop="openDeleteConfirmation(conclusion)"
                  title="Delete conclusion"
              />
            </div>
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
    <!-- Empty State shown when there are no conclusions -->
    <v-card v-else variant="tonal" class="mb-6 pa-4 text-center">
      <p class="mb-4">No conclusions have been added to this question yet.</p>
      <v-btn
        color="primary"
        @click="openEditModal(false)"
        :disabled="isQuestionVerified || isQuestionRejected || store.reportLocked"
      >
        <v-icon left class="mr-2">mdi-plus</v-icon>
        Add Your Conclusion
      </v-btn>
    </v-card>
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

  <!-- Delete Confirmation Modal -->
  <v-dialog v-model="showDeleteConfirmation" max-width="500px" width="auto">
    <v-card>
      <v-card-title class="text-h5"><v-icon icon="mdi-delete-outline" class="mr-2" />Are you sure?</v-card-title>
      <v-card-text>
        You are about to permanently delete this conclusion. This action cannot
        be undone.
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="closeDeleteConfirmation"
          :disabled="isDeleting"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          @click="confirmDelete"
          :loading="isDeleting"
        >
          Delete
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { useAppStore } from "@/stores/app"
import RestApiClient from "@/utils/RestApiClient"

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
      showDeleteConfirmation: false,
      conclusionToDelete: null,
      isDeleting: false,
      panels:
        this.question?.conclusions && this.question.conclusions.length > 0
          ? [this.question.conclusions[0].id]
          : ["fallback"],
    }
  },
  computed: {
    hasConclusions() {
      return this.question?.conclusions && this.question.conclusions.length > 0
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
      )
    },
  },
  methods: {
    openEventLog() {
      this.showEventLog = true
    },
    closeEventLog() {
      this.showEventLog = false
    },
    isEditable(conclusion) {
      // Not automated, not locked and owned by the current user
      return !conclusion.automated &&
             !this.store.reportLocked &&
             !this.isQuestionRejected &&
             conclusion.user && conclusion.user.username === this.store.currentUser
    },
    isDeletable(conclusion) {
      if (this.isQuestionVerified || this.isQuestionRejected || this.store.reportLocked) {
        return false
      }
      const isOwner = conclusion.user && conclusion.user.username === this.store.currentUser
      return conclusion.automated || isOwner
    },
    openEditModal(conclusion) {
      this.editingConclusion = conclusion
      this.showEditModal = true
    },
    handleModalClose() {
      this.showEditModal = false
      this.editingConclusion = null
      if (this.question?.id) {
        this.refreshQuestionById(this.question.id)
      }
    },
    openDeleteConfirmation(conclusion) {
      this.conclusionToDelete = conclusion
      this.showDeleteConfirmation = true
    },
    closeDeleteConfirmation() {
      this.showDeleteConfirmation = false
      this.conclusionToDelete = null
    },
    async confirmDelete() {
      this.isDeleting = true
      try {
        await RestApiClient.deleteQuestionConclusion(
          this.store.sketch.id,
          this.question.id,
          this.conclusionToDelete.id
        )

        this.store.setNotification({
          text: 'Conclusion successfully deleted.',
          type: 'success',
          icon: 'mdi-check-circle-outline',
        })
        this.closeDeleteConfirmation()
        // Refresh the question data to update the UI
        this.refreshQuestionById(this.question.id)

      } catch (error) {
        console.error('Error deleting conclusion:', error)
        this.store.setNotification({
          text: 'Unable to delete conclusion. Please try again.',
          type: 'error',
          icon: 'mdi-alert-circle-outline',
        })
      } finally {
        this.isDeleting = false
      }
    },
  },
  provide() {
    return {
      showEventLog: computed(() => this.showEventLog),
      closeEventLog: this.closeEventLog,
    }
  },
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
