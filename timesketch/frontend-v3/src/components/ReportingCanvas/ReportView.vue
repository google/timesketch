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
  <section>
    <header class="report-header px-6 pt-8 pb-8 mb-8 border-b-thin">
      <h2 class="mb-4 text-h3 font-weight-bold">Investigation Report</h2>

      <div class="d-flex align-center justify-space-between">
        <v-chip size="x-small" variant="outlined" class="px-2 py-2 rounded-l">
          Pre-generated Report by AI
        </v-chip>
        <div class="d-flex align-center ga-4">
          <v-btn variant="text" size="small" color="primary">
            <v-icon
              icon="mdi-download-circle-outline"
              class="mr-1"
              left
              small
            />
            Download</v-btn
          >
          <v-btn rounded color="primary"> Complete investigation</v-btn>
        </div>
      </div>
    </header>

    <form class="px-6 mb-10">
      <div class="report-form-group mb-6 w-50">
        <label for="summary" class="font-weight-bold">Name</label>
        <v-text-field
          hide-details="auto"
          id="name"
          name="name"
          variant="outlined"
          density="compact"
        ></v-text-field>
        <label for="Analyst" class="font-weight-bold">Analyst(s)</label>
        <v-text-field
          hide-details="auto"
          id="analyst"
          name="analyst"
          variant="outlined"
          density="compact"
        ></v-text-field>
      </div>
      <div class="report-form-group ga-6 mb-12 w-50">
        <p class="font-weight-bold">Finalized Date & Time</p>
        <p class="font-italic report-auto-timestamp">
          It will be automatically recorded upon completion.
        </p>
        <p class="font-weight-bold">Progress</p>
        <p>
          {{ completedQuestionsTotal }} / {{ questionsTotal }} questions
          finalized
        </p>
      </div>
      <div>
        <div class="d-flex justify-space-between">
          <label for="summary" class="text-h6 font-weight-bold mb-2 d-block"
            >Summary</label
          >
          <v-btn
            variant="text"
            size="small"
            color="primary"
            @click="$emit('regenerate-questions')"
            class="text-uppercase"
          >
            <v-icon icon="mdi-reload" class="mr-2" left small />
            Regenerate Summary</v-btn
          >
        </div>
        <v-textarea id="summary" name="summary" variant="outlined"></v-textarea>
      </div>
    </form>

    <div class="px-6">
      <h3 class="text-h6 font-weight-bold mb-5">Key Findings</h3>
      <ol class="questions-list">
        <li v-for="(question, index) in questions" class="question mb-10">
          <v-icon
            icon="mdi-check-circle"
            v-if="question.conclusions && question.conclusions.length > 0"
            small
            color="#34A853"
          />
          <p class="text-h6 font-weight-medium">
            {{ index + 1 }}. {{ question.name }}
          </p>
          <ul
            class="mt-4 ml-4"
            v-if="question.conclusions && question.conclusions.length > 0"
          >
            <li v-for="conclusion in question.conclusions">
              <p>{{ conclusion.conclusion }}</p>
            </li>
          </ul>
        </li>
      </ol>
    </div>
  </section>
</template>

<script setup>
const { completedQuestionsTotal, questionsTotal, questions } = defineProps({
  questions: Array,
  questionsTotal: Number,
  completedQuestionsTotal: Number,
});
</script>

<style scoped>
.questions-list {
  list-style: none;
}

.question::marker {
  font-size: inherit;
  font-weight: inherit;
}

.report-form-group {
  display: grid;
  grid-template-columns: 160px 1fr;
  row-gap: 10px;
  column-gap: 20px;
  align-items: center;
}

.report-header {
  background-color: #fafafa;
  border: 1px solid #dcdcdc;
}

.report-auto-timestamp {
  color: #5f6368;
}
</style>
