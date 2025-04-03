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
  <li class="question mb-10">
    <div class="d-inline-flex align-center justify-start">
      <v-icon
        icon="mdi-check-circle"
        v-if="isApproved"
        small
        color="#34A853"
        class="ml-2"
      />
    </div>
    <p class="text-h6 font-weight-medium">{{ order }}. {{ question.name }}</p>
    <ul class="my-4 ml-4" v-if="question.conclusion">
      <li>
        <p>{{ question.conclusion }}</p>
      </li>
    </ul>
    <QuestionActionsStrip
      :question="question"
      :reportLocked="reportLocked"
      :completed="isApproved"
      variant="a"
    />
  </li>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  props: { question: Object, index: Number, reportLocked: Boolean },
  inject: ["updateQuestion", "confirmRemoveQuestion"],
  data() {
    return {
      store: useAppStore(),
    };
  },
  computed: {
    isApproved() {
      if (
        this.store.report?.content?.approvedQuestions &&
        this.store.report?.content?.approvedQuestions.length > 0
      ) {
        return !!this.store.report.content.approvedQuestions.find(
          (approvedId) => approvedId === this.question.id
        );
      } else {
        return false;
      }
    },
    order() {
      return this.index + 1;
    },
  },
};
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
