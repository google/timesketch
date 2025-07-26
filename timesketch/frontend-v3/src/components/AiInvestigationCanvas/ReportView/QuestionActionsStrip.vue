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
  <v-card color="transparent" elevation="0" class="mb-6 d-flex align-center justify-space-between z-index-1000">
    <v-card-item>
      <v-btn
        v-if="isCompact"
        size="small"
        variant="text"
        color="primary"
        @click="store.setActiveQuestion(question)"
        >View Result Details <v-icon icon="mdi-arrow-right" class="ml-2" small
      /></v-btn>

      <!-- <p v-else class="font-weight-medium mb-1">
        Would you like to save the results to the report?
      </p> -->
    </v-card-item>
    <v-card-actions class="pa-0">
      <v-btn
        :disabled="reportLocked || isRejected"
        @click="rejectQuestion(question.id)"
        color="primary"
        size="small"
        title="Mark this question as not relevant"
        :class="!isCompact ? 'action-btn--large' : 'px-4'"
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
    }
  },
  computed: {
    isCompact() {
      return this.variant === 'compact'
    },
    isRejected() {
      return this.question?.status?.status === 'rejected'
    },
    backgroundColor() {
      if (this.isApproved || this.reportLocked || this.variant === 'approved') {
        return '#F8F9FA'
      } else {
        return '#3874CB'
      }
    },
    textColor() {
      if (this.variant === 'approved' || this.isConfirming || this.isApproved || this.reportLocked) {
        return 'primary'
      } else {
        return '#fff'
      }
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
.action-btn--large {
  height: 40px;
  border-radius: 8px !important;
  padding: 0 20px;
}
</style>
