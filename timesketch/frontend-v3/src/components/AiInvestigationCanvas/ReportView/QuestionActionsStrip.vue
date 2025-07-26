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
  <v-card color="transparent" elevation="0" class="mt-1 mb-6 d-flex align-center justify-space-between z-index-1000">
    <v-card-item v-if="isCompact">
      <v-btn size="small" variant="text" color="primary" @click="store.setActiveQuestion(question)"
        >View Result Details <v-icon icon="mdi-arrow-right" class="ml-2" small
      /></v-btn>

      <!-- <p v-else class="font-weight-medium mb-1">
        Would you like to save the results to the report?
      </p> -->
    </v-card-item>
    <div v-if="!isCompact">
      <div class="actions__item">
        <v-select
          v-model="selectedPriority"
          :class="[`actions__priority-select actions__priority-select--${selectedPriority}`]"
          color="var(--theme-ai-color-blue-500)"
          :items="priorityItems"
          item-title="label"
          item-value="key"
          density="compact"
          variant="outlined"
          hide-details
          placeholder="Priority"
          :disabled="isUpdatingPriority"
        />
      </div>
    </div>

    <v-card-actions class="pa-0">
      <v-btn
        :disabled="reportLocked || isRejected"
        @click="rejectQuestion(question.id)"
        color="primary"
        size="small"
        title="Mark this question as not relevant"
        :class="!isCompact ? 'actions__btn--large' : 'px-4'"
        >mark as not relevant</v-btn
      >
      <v-btn
        variant="flat"
        color="primary"
        @click="confirmAndSave()"
        :disabled="reportLocked || isApproved"
        size="small"
        :class="!isCompact ? 'action-btn--large' : 'px-4'"
      >
        Verify Question
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { useAppStore } from '@/stores/app'
import RestApiClient from '@/utils/RestApiClient'
import { getPriorityFromLabels } from '@/components/AiInvestigationCanvas/_utils/QuestionPriority'

export default {
  inject: ['updateQuestion'],
  props: {
    question: Object,
    index: Number,
    reportLocked: Boolean,
    isApproved: Boolean,
    variant: String,
  },
  data() {
    return {
      store: useAppStore(),
      isSubmitting: false,
      isConfirming: false,
      selectedPriority: this.priority,
      isUpdatingPriority: false,
      priorityItems: [
        { key: 'high', label: 'High Priority' },
        { key: 'medium', label: 'Medium Priority' },
        { key: 'low', label: 'Low Priority' },
      ],
    }
  },
  watch: {
    question: {
      handler() {
        this.selectedPriority = this.priority
      },
      immediate: true,
      deep: true,
    },
    async selectedPriority(newPriority, oldPriority) {
      if (newPriority === oldPriority) {
        return
      }

      this.isUpdatingPriority = true
      try {
        const labelName = `__ts_priority_${newPriority}`

        const response = await RestApiClient.updateQuestion(this.store.sketch.id, this.question.id, {
          priority: labelName,
        })

        // Update the question in the parent component's state
        this.updateQuestion(response.data.objects[0])

        this.store.setNotification({
          text: 'Question priority updated',
          icon: 'mdi-check-circle-outline',
          type: 'success',
        })
      } catch (error) {
        console.error(error)
        this.store.setNotification({
          text: 'Unable to update priority. Please try again.',
          icon: 'mdi-alert-circle-outline',
          type: 'error',
        })
        // Revert on failure
        this.selectedPriority = oldPriority
      } finally {
        this.isUpdatingPriority = false
      }
    },
  },
  computed: {
    isCompact() {
      return this.variant === 'compact'
    },
    isRejected() {
      return this.question?.status?.status === 'rejected'
    },
    priority() {
      return getPriorityFromLabels(this.question.labels)
    },
  },
  methods: {
    async confirmAndSave() {
      this.isConfirming = true

      try {
        const existingQuestions = Array.isArray(this.store.report?.content?.approvedQuestions)
          ? this.store.report?.content?.approvedQuestions
          : []

        await this.store.updateReport({
          approvedQuestions: Array.from(new Set([...existingQuestions, this.question.id])),
        })

        this.store.setNotification({
          text: 'Question approved',
          icon: 'mdi-check-circle-outline',
          type: 'success',
        })
      } catch (error) {
        console.error(error)
        this.store.setNotification({
          text: 'Unable to approve question',
          icon: 'mdi-close-circle-outline',
          type: 'error',
        })
      } finally {
        this.isConfirming = false
      }
    },
    async rejectQuestion(questionId) {
      try {
        this.isSubmitting = true

        // Update the question status to "rejected"
        await RestApiClient.updateQuestion(this.store.sketch.id, questionId, {
          status: 'rejected',
        })

        // Rerender with updated status
        const updatedQuestion = await RestApiClient.getQuestion(this.store.sketch.id, questionId)

        // Update the question in the store
        this.updateQuestion(updatedQuestion.data.objects[0])

        this.store.setActiveQuestion(null)

        this.store.setNotification({
          text: this.index ? `Question ${this.index + 1} has been rejected` : `This question has been rejected`,
          icon: 'mdi-minus-circle-outline',
          type: 'success',
        })
      } catch (error) {
        console.error(error)
        this.store.setNotification({
          text: 'Unable to reject question. Please try again.',
          icon: 'mdi-alert-circle-outline',
          type: 'error',
        })
      } finally {
        this.isSubmitting = false
      }
    },
  },
}
</script>

<style scoped>
.actions__btn--large {
  height: 40px;
  border-radius: 8px !important;
  padding: 0 20px;
}

.actions__priority-select {
  min-width: 80px;
  font-size: 14px;
  font-weight: 500;

  &:deep(input::placeholder) {
    opacity: 1 !important;
    color: var(--theme-ai-color-gray-700) !important;
    font-weight: 400;
    font-size: 12px;
  }

  &:deep(.v-field) {
    padding: 0 !important;
    font-size: 14px;
  }

  &:deep(.v-field__append-inner) {
    margin-right: 4px;
  }

  &:deep(.v-field__outline) {
    border-radius: 30px;
    z-index: -1;
    --v-field-border-opacity: 1;
  }

  &:deep(.v-field__input) {
    --v-input-control-height: 34px;
    --v-field-padding-start: 12px;
    --v-field-padding-end: 0px;
    --v-field-input-padding-top: 0px;
    --v-field-input-padding-bottom: 0px;
    --v-input-control-height: 26px;
    justify-content: center;
    white-space: nowrap;

    input {
      align-self: center;
      text-align: left;
      padding-left: 12px;
      left: 0;
    }
  }

  &:deep(.v-select__selection) {
    margin-inline-end: 0 !important;
    color: var(--theme-ai-color-gray-700) !important;
  }

  &:deep(.v-select__selection-text) {
    font-weight: 400 !important;
    font-size: 12px;
  }

  &:deep(.v-icon) {
    opacity: 1;
  }
}

.actions__priority-select--high {
  color: var(--theme-ai-color-red-300);

  &:deep(.v-field__outline) {
    background-color: var(--theme-ai-color-red-50);
  }

  &:deep(.v-select__selection-text),
  &:deep(.v-icon) {
    color: var(--theme-ai-color-red-900);
  }
}

.actions__priority-select--medium {
  color: var(--theme-ai-color-yellow-600);

  &:deep(.v-field__outline) {
    background-color: rgba(227, 116, 0, 0.15);
  }

  &:deep(.v-select__selection-text),
  &:deep(.v-icon) {
    color: #703a00;
  }
}

.actions__priority-select--low {
  color: var(--theme-ai-color-yellow-300);

  &:deep(.v-field__outline) {
    background-color: var(--theme-ai-color-yellow-50);
  }

  &:deep(.v-select__selection-text),
  &:deep(.v-icon) {
    color: #574100;
  }
}
</style>
