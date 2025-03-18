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
  <v-card
    :color="backgroundColor"
    elevation="0"
    class="mb-6 d-flex align-center justify-space-between"
  >
    <v-card-item>
      <v-btn
        v-if="variant === 'a'"
        rounded
        size="small"
        variant="text"
        color="primary"
        @click="store.setActiveQuestion(question)"
        >View Result Details <v-icon icon="mdi-arrow-right" class="ml-2" small
      /></v-btn>

      <p v-else class="font-weight-medium mb-1">
        Would you like to save the results to the report?
      </p>
    </v-card-item>

    <v-card-actions>
      <v-btn
        :disabled="reportLocked"
        @click="confirmRemoveQuestion(question.id)"
        :color="textColor"
        size="small"
        >Remove Question</v-btn
      >
      <v-btn
        rounded
        variant="flat"
        :color="textColor"
        @click="confirmAndSave()"
        :disabled="reportLocked || completed"
        size="small"
      >
        {{ completed ? "Saved" : "Confirm &amp; Save" }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  inject: ["confirmRemoveQuestion", "updateQuestion"],
  props: {
    question: Object,
    index: Number,
    reportLocked: Boolean,
    completed: Boolean,
    variant: String,
  },
  data() {
    return {
      store: useAppStore(),
      isSubmitting: false,
      isConfirming: false,
      riskLevel: this.question.risk_level,
    };
  },
  computed: {
    backgroundColor() {
      let defaultColor = this.variant === "a" ? "#F8F9FA" : "#3874CB";
      const lockedColor = this.variant === "b" ? "#3874CB" : "#F8F9FA";

      if (this.completed || this.reportLocked) {
        defaultColor = "#F8F9FA";
      }

      return defaultColor;
    },
    textColor() {
      let defaultColor = "#fff";

      if (this.isConfirming || this.completed || this.reportLocked) {
        defaultColor = "#primary";
      }

      return defaultColor;
    },
  },
  methods: {
    async confirmAndSave() {
      this.isConfirming = true;

      try {
        const existingQuestions =
          Array.isArray(this.store.report?.content?.approvedQuestions) || [];

        await this.store.updateReport({
          approvedQuestions: Array.from(
            new Set([...existingQuestions, this.question.id])
          ),
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
  },
};
</script>
