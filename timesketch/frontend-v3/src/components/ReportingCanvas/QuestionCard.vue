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
  <v-list-item :class="listItemClasses" @click="store.setActiveQuestion(id)">
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
      <div class="d-flex ga-2">
        <v-chip
          v-if="risk"
          size="x-small"
          :color="riskColor"
          class="text-uppercase px-1 py-1 rounded-sm font-weight-medium"
        >
          {{ risk }}
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

<script setup>
import { useAppStore } from "@/stores/app";
import { computed } from "vue";

const store = useAppStore();

const { user, name, risk, conclusions, type, id, updated_at } = defineProps({
  name: String,
  type: String,
  risk: String,
  conclusions: Array,
  updated_at: String,
  id: Number,
  user: Object
});

const completed = computed(() => conclusions && conclusions.length > 0);

const riskColor = computed(() => {
  switch (risk) {
    case "high":
      return "#D9302533";
    case "med":
      return "#E3740033";
    case "low":
      return "#890E06";
    default:
      return "#3874CB33";
  }
});

const listItemClasses = computed(() => ({
  "is--active": id === store.activeContext.question,
  "border-b-sm": true,
  "px-4 py-8": true,
  "border-right-md": true,
}));
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
