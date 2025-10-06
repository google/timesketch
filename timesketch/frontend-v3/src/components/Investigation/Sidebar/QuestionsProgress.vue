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
  <v-card v-if="isGenerating" class="progress-card" :elevation="0">
    <div class="flex-grow-1 flex-shrink-1">
      <div class="d-flex justify-space-between ga-1 align-baseline mb-2 flex-wrap">
        <h4>
          AI Analysis in progress
          <p class="text-body-2 mb-1">{{ currentMessage }}</p>
        </h4>
        <p v-if="questionsTotal" class="text-body-2">
          <span class="font-weight-bold">{{ questionsTotal }}</span>
          questions created
        </p>
      </div>
      <v-progress-linear
        class="progress-card__bar"
        width="100%"
        height="12"
        color="var(--theme-ai-color-ts-blue)"
        bg-color="var(--theme-ai-color-blue-100)"
        bg-opacity="1"
        indeterminate
        rounded="xl"
      ></v-progress-linear>
    </div>
    <v-card-actions class="flex-0-0 pa-0 h-auto progress-card__cta">
      <v-btn
        variant="outlined"
        class="ai-inline-cta"
        @click="toggleModal"
        :disabled="reportLocked || questionsTotal === 0"
      >
        Create Question
      </v-btn>
    </v-card-actions>
  </v-card>
  <v-card v-else class="progress-card" :elevation="0">
    <div class="flex-grow-1">
      <div class="d-flex justify-space-between ga-1 align-baseline mb-2 flex-wrap">
        <h4>Progress</h4>
        <p v-if="questionsTotal" class="text-body-2 text-no-wrap">
          <span class="font-weight-bold">{{ completedQuestionsTotal }} / {{ questionsTotal }}</span>
          questions answered
        </p>
      </div>
      <v-progress-linear
        class="progress-card__bar"
        height="12"
        width="100%"
        :color="percentageCompleted === 100 ? 'var(--theme-ai-color-green-500)' : 'var(--theme-ai-color-ts-blue)'"
        bg-color="var(--theme-ai-color-blue-100)"
        bg-opacity="1"
        :model-value="percentageCompleted"
        rounded="xl"
      ></v-progress-linear>
    </div>
    <v-card-actions class="flex-0-0 pa-0 h-auto progress-card__cta">
      <v-btn
        variant="outlined"
        class="ai-inline-cta"
        @click="toggleModal"
        :disabled="reportLocked || questionsTotal === 0"
      >
        Create Question
      </v-btn>
    </v-card-actions>
  </v-card>
  <v-dialog transition="dialog-bottom-transition" v-model="showModal" width="auto">
    <AddQuestionModal @close-modal="toggleModal" />
  </v-dialog>
</template>

<script>
import { useAppStore } from '@/stores/app'

export default {
  data() {
    return {
      store: useAppStore(),
      showModal: false,
      // Using a small UX trick here since we don't get the correct status from
      // the AI agent in the frontend yet.
      loadingMessages: [
        'Calibrating the anomaly detector...',
        'Sifting through heaps of data...',
        'Connecting seemingly unrelated events...',
        'Looking for needles...',
        'Asking the agent about evil bits...',
        'Consulting the forensic agent...',
        'Untangling spaghetti logs...',
        'Following the digital breadcrumbs...',
        'Asking questions...',
        'Polishing the findings...',
        'Going down the rabbit hole...',
        'Reticulating timelines.',
        'Poking up the analysis agents...',
        'Reconstructing the event sequence...',
        'Dusting for digital fingerprints...',
        'Correlating events across timelines...',
        'Searching for anomalous patterns...',
        'Generating new hypotheses...',
        'Identifying suspicious outliers...',
        'Building a chain of evidence...',
        'Normalizing timestamps...',
        'Cooling the reasoning engine...',
      ],
      currentMessage: 'Log Analyzer is working...',
      timerIds: [],
      shuffledMessages: [],
    }
  },
  props: {
    questionsTotal: Number,
    completedQuestionsTotal: Number,
    isGenerating: Boolean,
    reportLocked: Boolean,
  },
  methods: {
    toggleModal() {
      this.showModal = !this.showModal
    },
    shuffleArray(array) {
      for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[array[i], array[j]] = [array[j], array[i]]
      }
      return array
    },
    updateRandomMessage() {
      if (this.shuffledMessages.length === 0) {
        this.shuffledMessages = this.shuffleArray([...this.loadingMessages])
      }
      this.currentMessage = this.shuffledMessages.pop()
      this.scheduleNextRandomMessage()
    },
    scheduleNextRandomMessage() {
      const randomDelay = Math.random() * (12000 - 5000) + 5000
      const timerId = setTimeout(() => {
        if (this.isGenerating) {
          this.updateRandomMessage()
        }
      }, randomDelay)
      this.timerIds.push(timerId)
    },
    startLoadingSequence() {
      this.currentMessage = 'Sending events...'
      const phase1Timer = setTimeout(() => {
        if (!this.isGenerating) return

        this.currentMessage = 'Preparing the agents...'
        const phase2Timer = setTimeout(() => {
          if (!this.isGenerating) return
          this.updateRandomMessage()
        }, 10000)
        this.timerIds.push(phase2Timer)
      }, 20000)
      this.timerIds.push(phase1Timer)
    },
    stopLoadingSequence() {
      this.timerIds.forEach((id) => clearTimeout(id))
      this.timerIds = []
      this.currentMessage = 'Log Analyzer is working...'
      this.shuffledMessages = []
    },
  },
  computed: {
    percentageCompleted() {
      return this.questionsTotal ? (this.completedQuestionsTotal / this.questionsTotal) * 100 : 0
    },
  },
  watch: {
    isGenerating(newValue) {
      if (newValue) {
        this.startLoadingSequence()
      } else {
        this.stopLoadingSequence()
      }
    },
  },
  beforeUnmount() {
    this.stopLoadingSequence()
  },
}
</script>

<style scoped>
.progress-card {
  padding: 17px 20px 16px;
  border-radius: 8px;
  border: 1px solid var(--theme-ai-color-gray-100);
  background-color: var(--theme-ai-color-white);
  margin-bottom: 16px;
  gap: 30px;
  display: flex;
  flex-wrap: nowrap;
  justify-content: center;
}

.progress-card__cta {
  min-height: auto;
}

.progress-card__bar {
  &:deep(.v-progress-linear__determinate) {
    border-radius: 24px;
  }
}
</style>
<style scoped>
.progress-card {
  padding: 17px 20px 20px;
  border-radius: 8px;
  border: 1px solid var(--theme-ai-color-gray-100);
  background-color: var(--theme-ai-color-white);
  margin-bottom: 16px;
  gap: 30px;
  display: flex;
  flex-wrap: nowrap;
  justify-content: center;
}

.progress-card__cta {
  min-height: auto;
}

.progress-card__bar {
  &:deep(.v-progress-linear__determinate) {
    border-radius: 24px;
  }
}
</style>
