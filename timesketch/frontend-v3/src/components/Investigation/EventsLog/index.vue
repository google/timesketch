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
  <v-toolbar>
    <v-toolbar-title class="font-weight-bold">{{ toolbarTitle }}</v-toolbar-title>
    <form
      @submit.prevent="handleSubmission"
      class="search-form w-50 position-relative"
    >
      <v-text-field
        hide-details="auto"
        id="name"
        name="name"
        variant="outlined"
        density="compact"
        placeholder="Enter a query"
        :disabled="store.reportLocked"
        class="bg-white"
        v-model="queryString"
      ></v-text-field>
      <v-btn type="submit" class="search-button position-absolute">
        <v-icon icon="mdi-magnify"
      /></v-btn>
    </form>
    <div class="v-spacer"></div>
    <v-btn text @click="$emit('close-drawer')">
      <v-icon icon="mdi-close" small />
    </v-btn>
  </v-toolbar>
  <div class="px-8 py-4 overflow-auto">
    <EventList
      v-if="conclusionId || isDraftMode"
      :conclusionId="conclusionId"
      :disableDownload="true"
      :disableHistogram="true"
      :disableSettings="true"
      :disableColumns="true"
      :disableStarring="true"
      :disableSaveSearch="true"
      :disableTagging="true"
      :disableIQFacts="false"
      :queryRequest="queryRequest"
      :isDraftMode="isDraftMode"
      @event-selected-for-draft="$emit('event-selected-for-draft', $event)"
    />
  </div>
</template>

<script>
import { useAppStore } from "@/stores/app"

export default {
  emits: ['event-selected-for-draft', 'close-drawer'],
  props: {
    conclusionId: Number,
    existingEvents: {
      type: Array,
      default: () => [],
    },
    isDraftMode: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      store: useAppStore(),
      queryString: "",
      queryRequest: {
        queryString: "*",
        queryFilter: {
          from: 0,
          terminate_after: 10,
          size: 10,
          indices: ["_all"],
          order: "asc",
          chips: [],
        },
      },
    }
  },
  computed: {
    toolbarTitle() {
      return this.isDraftMode ? 'Link Supporting Events' : 'Add Additional Supporting Events'
    }
  },
  methods: {
    handleSubmission() {
      this.queryRequest = {
        ...this.queryRequest,
        queryString: this.queryString,
      }
    },
  },
}
</script>

<style scoped>
.search-button {
  right: 0;
  top: 50%;
  transform: translateY(-50%);
}
</style>
