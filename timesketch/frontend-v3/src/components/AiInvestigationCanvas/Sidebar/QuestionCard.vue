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
  <v-list-item
    :class="listItemClasses"
    :active="isActive"
    @click="setActiveQuestion()"
  >
    <div class="d-flex ga-6 align-center justify-md-space-between flex-wrap">
      <div class="d-flex ga-6 align-center">
        <v-icon
          icon="mdi-account-check-outline"
          color="#757575"
          v-if="user.name"
          small
          left
        />
        <v-icon icon="mdi-creation" v-else small color="#757575" />
        <p class="font-weight-medium">{{ index }} : {{ name }}</p>
      </div>
      <div class="d-flex ga-2 align-center flex-1-1-100">
        <v-chip
          v-if="priority"
          :class="['chip', priorityColor]"
          small
          label
          :title="`Priority: ${priority}`"
        >
          {{ priority }} Priority
        </v-chip>
        <v-chip
          v-if="isApproved"
          small
          label
          title="Verified"
          :class="['chip', 'chip--verified']"
        >
          <v-icon icon="mdi-check-circle-outline" start></v-icon>
          Verified
        </v-chip>
      </div>
    </div>
  </v-list-item>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  props: {
    name: String,
    type: String,
    conclusion: String,
    conclusionSummary: String,
    conclusions: Array,
    updatedAt: String,
    id: Number,
    user: Object,
    index: Number,
    labels: Array,
  },
  data() {
    return {
      store: useAppStore(),
    };
  },
  methods: {
    setActiveQuestion() {
      this.store.setActiveQuestion({
        user: this.user,
        name: this.name,
        conclusionSummary: this.conclusionSummary,
        conclusions: this.conclusions,
        type: this.type,
        id: this.id,
        updatedAt: this.updated_at,
        completed: this.completed,
      });
    },
  },
  computed: {
    isActive() {
      return this.store.activeContext.question?.id
        ? this.id === this.store.activeContext.question?.id
        : false;
    },

    isApproved() {
      return !!this.store.report?.content?.approvedQuestions?.find(
        (approvedId) => approvedId === this.id
      );
    },

    listItemClasses() {
      return {
        "is--active": this.isActive,
        "border-b-sm": true,
        "px-4 py-8": true,
        "border-right-md": true,
      };
    },
    priority() {
      if (!this.labels || !Array.isArray(this.labels)) {
        return null;
      }
      const priorityPrefix = "__ts_priority_";
      const priorityLabel = this.labels.find((label) =>
        label.name.startsWith(priorityPrefix)
      );

      return priorityLabel
        ? priorityLabel.name.replace(priorityPrefix, "")
        : null;
    },
    priorityColor() {
      if (!this.priority) return "chip--none";
      switch (this.priority.toLowerCase()) {
        case "high":
          return "chip--high";
        case "medium":
          return "chip--medium";
        case "low":
          return "chip--low";
        default:
          return "chip--none";
      }
    },
  },
};
</script>

<style scoped>
.is--active {
  position: relative;

  &::after {
    content: "";
    display: block;
    height: 100%;
    width: 6px;
    background-color: #3874cb;
    position: absolute;
    opacity: 1;
    outline: none;
    right: 0;
    left: auto;
    top: 0;
    border-radius: 0;
    border: none;
  }
}

.chip {
  --v-chip-height: 20px;
  padding: 0 4px;
  font-weight: 700;
  font-size: 10px;
  line-height: 1;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;

  &:deep(.v-chip__underlay) {
    display: none !important;
  }

  &:has(.v-icon--start) {
    padding-left: 11px;

    &:deep(.v-icon--start) {
      margin-inline-end: 4px;
    }
  }

  &.chip--high {
    background-color: var(--theme-ai-color-red-100);
    color: var(--theme-ai-color-red-900);
  }

  &.chip--medium {
    background-color: #f9e3cc;
    color: #703a00;
  }

  &.chip--low {
    background-color: var(--theme-ai-color-yellow-100);
    color: #574100;
  }

  &.chip--none {
    background-color: var(--theme-ai-color-gray-100);
    color: var(--theme-ai-color-gray-900);
  }

  &.chip--verified {
    background-color: var(--theme-ai-color-green-100);
    color: var(--theme-ai-color-green-900);
  }
}
</style>
