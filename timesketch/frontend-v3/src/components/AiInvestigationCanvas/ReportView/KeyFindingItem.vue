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
      <RiskLevelControl
        :riskLevel="riskLevel"
        @update:riskLevel="($event) => (riskLevel = $event)"
      />
      <v-icon
        icon="mdi-check-circle"
        v-if="completed"
        small
        color="#34A853"
        class="ml-2"
      />
    </div>
    <p class="text-h6 font-weight-medium">{{ order }}. {{ question.name }}</p>
    <!-- <ul class="my-4 ml-4" v-if="question.conclusion">
      <li>
        <p>{{ question.conclusion }}</p>
      </li>
    </ul> -->

    <v-card
      color="#F8F9FA"
      elevation="0"
      class="mb-6 d-flex align-center justify-space-between"
    >
      <v-card-item>
        <v-btn
          rounded
          size="small"
          variant="text"
          color="primary"
          @click="store.setActiveQuestion(question)"
          >View Result Details
          <v-icon icon="mdi-arrow-right" class="ml-2" small
        /></v-btn>
      </v-card-item>

      <v-card-actions>
        <v-btn
          :disabled="reportedLocked"
          @click="confirmRemoveQuestion(question.id)"
          color="primary"
          size="small"
          >Remove Question</v-btn
        >
        <v-btn
          rounded
          variant="flat"
          color="primary"
          @click="confirmAndSave()"
          :disabled="reportedLocked"
          size="small"
          >Confirm &amp; Save</v-btn
        >
      </v-card-actions>
    </v-card>
  </li>
</template>

<script>
import { useAppStore } from '@/stores/app';

export default {
  inject: ['confirmRemoveQuestion', 'updateQuestion'],
  props: { question: Object, index: Number, reportedLocked: Boolean },
  data() {
    return {
      store: useAppStore(),
      isSubmitting: false,
      isConfirming: false,
      riskLevel: this.question.risk_level,
    };
  },
  methods: {
    async confirmAndSave() {
      this.isConfirming = true;

      try {
        const existingQuestions =
        this.store.report?.content?.approvedQuestions || [];

        await this.store.updateReport({
          approvedQuestions: Array.from(new Set([...existingQuestions, this.question.id]))
        });

        this.store.setNotification({
          text: `Question approved`,
          icon: "mdi-check-circle-outline",
          type: "success",
        });
      } catch (error) {
        console.error(error);
        
        this.store.setNotification({
          text: `Unable to approve question`,
          icon: "mdi-close-circle-outline",
          type: "error",
        });
      } finally {
        this.isConfirming = false;
      }
    },
    async downloadReport() {
      // keep it loca
    },
    async fileReport() {
      // wrap it up
    },
    async reqenerateSummary() {
      // I don't like stale
    },
  },
  computed: {
    completed() {
      let isApproved = false;

      if (
        this.store.report?.content?.approvedQuestions &&
        this.store.report?.content?.approvedQuestions.length > 0
      ) {
        isApproved = !!this.store.report.content.approvedQuestions.find(
          (approvedId) => approvedId === this.question.id
        );
      }

      return isApproved;
    },
    order() {
      return this.index;
    },
  },
  watch: {
    riskLevel(riskLevel) {
      this.riskLevel = riskLevel;
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
