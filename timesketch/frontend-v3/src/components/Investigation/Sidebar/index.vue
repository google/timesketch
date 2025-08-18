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
  <v-navigation-drawer
    v-if="isAiRouteActive"
    :rail="rail"
    :rail-width="52"
    :width="473"
    permanent
    class="ai-investigation-canvas__sidebar"
  >
    <QuestionsListLoader v-if="isLoading" />
    <template v-else>
      <div class="ai-investigation-canvas__sidebar-content">
        <v-btn
          icon
          @click.stop="toggleRail"
          class="mb-2 position-absolute top-0 right-0"
          width="52"
          height="55"
          style="z-index: 10"
          elevation="0"
          rounded
        >
          <v-icon :icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'" :color="'var(--theme-ai-color-ts-blue)'" />
        </v-btn>
        <div v-if="!rail">
          <div>
            <h2 class="mb-3 h5">Questions</h2>
            <QuestionsProgress
              :questionsTotal="verifiedTotal"
              :completedQuestionsTotal="completedQuestionsTotal"
              :isGenerating="isGenerating"
            />
          </div>

          <QuestionsListLoader v-if="isLoading" />
          <QuestionsList :questions="sortedQuestions" :questionsTotal="questionsTotal" :reportLocked="reportLocked" />
        </div>
      </div>
    </template>
  </v-navigation-drawer>
</template>

<script>
import { useRoute } from 'vue-router'

export default {
  props: {
    questionsTotal: {
      type: Number,
      default: 0,
    },
    completedQuestionsTotal: {
      type: Number,
      default: 0,
    },
    verifiedTotal: {
      type: Number,
      default: 0,
    },
    isLoading: {
      type: Boolean,
      default: true,
    },
    isGenerating: Boolean,
    questions: Array,
    reportLocked: Boolean,
  },
  data() {
    return {
      rail: false,
      route: useRoute(),
    }
  },
  computed: {
    isAiRouteActive() {
      return this.route.name === 'Investigation'
    },
    sortedQuestions() {
      return this.questions && this.questions.length > 0
        ? [...this.questions.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))]
        : []
    },
  },
  methods: {
    toggleRail() {
      this.rail = !this.rail
    },
  },
}
</script>

<style scoped>
.ai-investigation-canvas__sidebar {
  background-color: var(--theme-ai-color-gray-50);
}

.ai-investigation-canvas__sidebar-content {
  width: 473px;
  padding: 33px 12px 12px;
}
</style>
