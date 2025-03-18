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
    <div class="d-flex ga-6 align-center justify-md-space-between">
      <div class="d-flex ga-6 align-center">
        <v-icon
          icon="mdi-account-check-outline"
          color="#757575"
          v-if="user"
          small
          left
        />
        <v-icon icon="mdi-creation" v-else small color="#757575" />
        <p class="font-weight-medium">{{ name }}</p>
      </div>
      <div class="d-flex ga-2 align-center">
        <v-chip
          v-if="riskLevel"
          size="x-small"
          :color="riskColor"
          class="text-uppercase px-1 py-1 rounded-sm font-weight-bold"
        >
          {{ riskLevel }}
        </v-chip>
        <v-icon
          icon="mdi-check-circle"
          v-if="completed"
          small
          color="#34A853"
        />
      </div>
    </div>
  </v-list-item>
</template>

<script>
import { useAppStore } from "@/stores/app";

const riskColors = {
  high: "#D93025",
  medium: "#E37400",
  low: "#FBBC04",
  clean: "#3874CB",
};

export default {
  props: {
    name: String,
    type: String,
    conclusion: String,
    observables: Array,
    updated_at: String,
    risk_level: String,
    id: Number,
    user: Object,
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
        riskLevel: this.riskLevel,
        observables: this.observables,
        conclusion: this.conclusion,
        type: this.type,
        id: this.id,
        updated_at: this.updated_at,
        completed: this.completed,
      });
    },
  },
  computed: {
    sortedQuestions() {
      return this.questions && this.questions.length > 0
        ? [
            ...this.questions.sort(
              (a, b) => new Date(b.updated_at) - new Date(a.updated_at)
            ),
          ]
        : [];
    },

    isActive() {
      return this.store.activeContext.question?.id
        ? this.id === this.store.activeContext.question?.id
        : false;
    },

    completed() {
      let isApproved = false;

      if (
        this.store.report?.content?.approvedQuestions &&
        this.store.report?.content?.approvedQuestions.length > 0
      ) {
        isApproved = !!this.store.report.content.approvedQuestions.find(
          (approvedId) => approvedId === this.id
        );
      }

      return isApproved;
    },

    riskColor() {
      return riskColors[riskLevel];
    },

    listItemClasses() {
      return {
        "is--active": this.isActive,
        "border-b-sm": true,
        "px-4 py-8": true,
        "border-right-md": true,
      };
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
</style>
