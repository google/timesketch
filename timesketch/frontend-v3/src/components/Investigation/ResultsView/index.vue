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
  <section>
    <header class="question__header pa-6">
      <v-btn
        variant="text"
        size="small"
        color="primary"
        class="ml-n3"
        :disabled="disableCta"
        @click="store.setActiveQuestion(null)"
      >
        <v-icon size="large" icon="mdi-arrow-left mr-2" />
        Report
      </v-btn>

      <h1 class="question__heading">
        {{ question.name }}
      </h1>

      <QuestionActionsStrip v-if="!reportLocked" :isApproved="isApproved" :question="question" variant="detailed" />
    </header>

    <div class="pa-6 mb-6">
      <ConclusionSummary :question="question" />
    </div>
    <ConclusionsAccordion :question="question" />
  </section>
</template>

<script>
import { useAppStore } from '@/stores/app'
import ConclusionSummary from './ConclusionSummary.vue'

export default {
  props: {
    question: Object,
    reportLocked: Boolean,
    isLoading: Boolean,
  },
  inject: ['updateQuestion', 'confirmRemoveQuestion'],
  data() {
    return {
      store: useAppStore(),
      panels:
        this.question.conclusions && this.question.conclusions.length
          ? [this.question.conclusions[0].id]
          : ['fallback'],
    }
  },
  computed: {
    disableCta() {
      return !this.store.activeContext.question?.id
    },
    isApproved() {
      return this.question?.status?.status === 'verified'
    },
  },
}
</script>

<style scoped>
.questions-list {
  list-style: none;
}

.question::marker {
  font-size: inherit;
  font-weight: inherit;
}

.question__header {
  background-color: var(--theme-ai-color-gray-50);
  border-bottom: 1px solid var(--theme-ai-color-gray-100);
}

.question__heading {
  font-size: 34px;
  font-weight: 600;
  line-height: 1.2;
  max-width: 594px;
  margin-top: 32px;
  text-wrap: pretty;
}
</style>
