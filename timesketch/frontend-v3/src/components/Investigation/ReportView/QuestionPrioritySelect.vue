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
  <v-select
    v-model="selectedPriority"
    :class="['question-priority-select', `question-priority-select--${selectedPriority}`]"
    color="var(--theme-ai-color-blue-500)"
    :items="priorityItems"
    item-title="label"
    item-value="key"
    density="compact"
    variant="outlined"
    hide-details
    placeholder="Priority"
    :loading="isUpdating"
    :disabled="isUpdating"
    @update:model-value="handlePriorityChange"
  />
</template>

<script>
import { getPriorityFromLabels } from '@/components/Investigation/_utils/QuestionPriority.js'
import { useAppStore } from '@/stores/app'
import RestApiClient from '@/utils/RestApiClient'

export default {
  props: {
    question: {
      type: Object,
      required: true,
    },
  },
  inject: ['updateQuestion'],
  data() {
    return {
      store: useAppStore(),
      selectedPriority: getPriorityFromLabels(this.question.labels),
      isUpdating: false,
      priorityItems: [
        { key: 'high', label: 'High Priority' },
        { key: 'medium', label: 'Medium Priority' },
        { key: 'low', label: 'Low Priority' },
      ],
    }
  },
  computed: {
    priority() {
      return getPriorityFromLabels(this.question.labels)
    },
  },
  watch: {
    // When the question prop changes externally, this watcher updates the
    // component's local state to ensure the UI is always in sync.
    priority(newVal) {
      if (this.selectedPriority !== newVal) {
        this.selectedPriority = newVal
      }
    },
  },
  methods: {
    async handlePriorityChange(newPriority) {
      const oldPriority = this.priority
      if (newPriority === oldPriority || !newPriority) {
        return
      }

      this.isUpdating = true
      try {
        const labelName = `__ts_priority_${newPriority}`

        const response = await RestApiClient.updateQuestion(this.store.sketch.id, this.question.id, {
          priority: labelName,
        })

        // Use the injected function to update the parent state.
        // This will trigger the prop change and the watcher.
        this.updateQuestion(response.data.objects[0])

        this.store.setNotification({
          text: 'Question priority updated.',
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
        // On failure, revert the selection back to the original value
        this.selectedPriority = oldPriority
      } finally {
        this.isUpdating = false
      }
    },
  },
}
</script>

<style scoped>
.question-priority-select {
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

.question-priority-select--high {
  color: var(--theme-ai-color-red-300);

  &:deep(.v-field__outline) {
    background-color: var(--theme-ai-color-red-50);
  }

  &:deep(.v-select__selection-text),
  &:deep(.v-icon) {
    color: var(--theme-ai-color-red-900);
  }
}

.question-priority-select--medium {
  color: var(--theme-ai-color-yellow-600);

  &:deep(.v-field__outline) {
    background-color: rgba(227, 116, 0, 0.15);
  }

  &:deep(.v-select__selection-text),
  &:deep(.v-icon) {
    color: #703a00;
  }
}

.question-priority-select--low {
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
