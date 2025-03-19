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
  <v-toolbar>
    <v-toolbar-title class="font-weight-bold">Add More Facts</v-toolbar-title>
    <v-text-field
      hide-details="auto"
      id="name"
      name="name"
      v-model="name"
      variant="outlined"
      density="compact"
      placeholder="Enter a query"
      :disabled="reportLocked"
      class="bg-white"
    ></v-text-field>
    <div class="v-spacer"></div>
    <v-btn text @click="closeEventLog()">
      <v-icon icon="mdi-close" small />
    </v-btn>
  </v-toolbar>
  <div class="pa-8">
    <EventsList 
    :disableToolbar="true"
    :showAddToFindings="true"
    />
  </div>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  inject: ["closeEventLog"],
  data() {
    return {
      store: useAppStore(),
    };
  },
};
</script>
