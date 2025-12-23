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
  <v-card class="pa-4 pt-5" min-height="800px">
    <v-card-title class="pl-6">Settings</v-card-title>
    <v-list class="pr-3" v-if="settings" two-line subheader flat>
      <v-list-subheader class="ml-3">Layout</v-list-subheader>
      <v-list-item>
        <div class="d-flex align-center pl-3">
          <v-switch v-model="settings.showLeftPanel" color="primary" @change="saveSettings()" hide-details></v-switch>
          <div class="pl-5">
            <v-list-item-title>Show side panel</v-list-item-title>
            <v-list-item-subtitle
              >Select if the side panel should be expanded or collapsed by default</v-list-item-subtitle
            >
          </div>
        </div>
      </v-list-item>
      <v-list-item v-if="systemSettings.LLM_PROVIDER">
        <div class="d-flex align-center pl-3">
          <v-switch v-model="settings.generateQuery" color="primary" @change="saveSettings()"></v-switch>
          <div class="pl-5">
            <v-list-item-title>AI generated queries</v-list-item-title>
            <v-list-item-subtitle
              >Select to enable experimental AI query suggestions for DFIQ questions</v-list-item-subtitle
            >
          </div>
        </div>
      </v-list-item>
    </v-list>
  </v-card>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import { useAppStore } from "@/stores/app";

const DEFAULT_SETTINGS = {
  showLeftPanel: true,
}

export default {
  data() {
    return {
      appStore: useAppStore(),
      settings: {
        showLeftPanel: true,
        generateQuery: true,
      },
    }
  },
  computed: {
    sketch() {
      return this.appStore.sketch
    },
    systemSettings() {
      return this.appStore.systemSettings
    },
    userSettings() {
      return this.appStore.settings
    },
  },
  methods: {
    saveSettings() {
      ApiClient.saveUserSettings(this.settings)
        .then(() => this.appStore.updateUserSettings())
        .catch((error) => {
          console.error(error)
        })
    },
  },
  mounted() {
    this.settings = { ...this.userSettings }
    // Set default values when the users don't have any settings saved.
    if (this.settings && !Object.keys(this.settings).length) {
      this.settings = { ...DEFAULT_SETTINGS }
      this.saveSettings()
    }
  },
}
</script>

<style scoped>
.example {
  color: red;
}
</style>
