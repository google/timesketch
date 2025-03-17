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
  <QuestionsListLoader v-if="isLoading" />
  <v-col
    v-else
    cols="12"
    md="6"
    lg="4"
    class="reporting-canvas__sidebar bg-grey-lighten-4 pa-4 fill-height overflow-hidden"
  >
    <div>
      <h2 class="mb-5 h5">Questions</h2>
      <QuestionsProgress
        :questionsTotal="questionsTotal"
        :completedQuestionsTotal="completedQuestionsTotal"
      />
    </div>
  </v-col>
</template>

<style scoped>
.reporting-canvas__sidebar {
  display: grid;
  grid-template-rows: auto auto 1fr auto;
}
</style>

<script>
import QuestionsListLoader from "../Loaders/QuestionsListLoader.vue";
import QuestionsProgress from "./QuestionsProgress.vue";

export default {
  props: {
    questionsTotal: Number,
    completedQuestionsTotal: Number,
    isLoading: Boolean,
  },
};
</script>
