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
  <v-card class="pa-4 d-flex ga-2 mb-10">
    <div class="flex-grow-1">
      <div class="d-flex justify-space-between">
        <h4 class="mb-2">Progress</h4>
        <p>
          <span class="font-weight-bold"
            >{{ completedQuestionsTotal }}/{{ questionsTotal }}</span
          >
          questions finalized
        </p>
      </div>
      <v-progress-linear
        height="12"
        bg-color="#4F378A"
        color="#4F378A"
        :model-value="percentageCompleted"
        rounded="xl"
      ></v-progress-linear>
    </div>
    <v-card-actions class="flex-grow-0">
      <v-spacer></v-spacer>
      <v-btn variant="flat" size="small" color="primary" @click="console.log('View Report')">View Report</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
const { questionsTotal, completedQuestionsTotal, percentageCompleted } =
  defineProps({
    questionsTotal: Number,
    completedQuestionsTotal: Number,
    percentageCompleted: Number,
  });
</script>
