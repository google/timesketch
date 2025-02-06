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
  <v-card class="pa-4" min-height="800px">
    <v-card-title>Settings</v-card-title>
    <v-list class="px-3" v-if="settings" two-line subheader flat>
      <v-subheader>Layout</v-subheader>
      <v-list-item>
        <v-list-item-action>
          <v-switch v-model="settings.showLeftPanel" color="primary" @change="saveSettings()"></v-switch>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>Show side panel</v-list-item-title>
          <v-list-item-subtitle
            >Select if the side panel should be expanded or collapsed by default</v-list-item-subtitle
          >
        </v-list-item-content>
      </v-list-item>

      <!-- AI Powered Features Main Setting -->
      <v-list-item v-if="systemSettings.LLM_PROVIDER">
        <v-list-item-action>
          <v-switch v-model="settings.aiPoweredFeaturesMain" color="primary" @change="updateAiFeatures" ></v-switch>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>AI powered features (experimental)</v-list-item-title>
          <v-list-item-subtitle>Main switch to enable or disable all experimental AI features</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>

      <!-- Child Setting: Event Summarization -->
      <v-list-item v-if="systemSettings.LLM_PROVIDER">
        <v-list-item-action class="ml-8"> 
          <v-switch
            v-model="settings.eventSummarization"
            color="primary"
            @change="saveSettings()"
            :disabled="!settings.aiPoweredFeaturesMain"
          ></v-switch>
        </v-list-item-action>
        <v-list-item-content class="ml-8"> 
          <v-list-item-title>Event summarization</v-list-item-title>
          <v-list-item-subtitle
            >Enable AI powered summarization of events</v-list-item-subtitle
          >
        </v-list-item-content>
      </v-list-item>

      <!-- Child Setting: AI Generated Queries -->
      <v-list-item v-if="systemSettings.LLM_PROVIDER">
        <v-list-item-action class="ml-8">
          <v-switch
            v-model="settings.generateQuery"
            color="primary"
            @change="saveSettings()"
            :disabled="!settings.aiPoweredFeaturesMain"
          ></v-switch>
        </v-list-item-action>
        <v-list-item-content class="ml-8">
          <v-list-item-title>AI generated queries</v-list-item-title>
          <v-list-item-subtitle
            >Enable experimental AI query suggestions for DFIQ questions</v-list-item-subtitle
          >
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </v-card>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

const DEFAULT_SETTINGS = {
  showLeftPanel: true,
  aiPoweredFeaturesMain: false,
  eventSummarization: false,
  generateQuery: false,
}

export default {
  data() {
    return {
      settings: {
        showLeftPanel: true,
        aiPoweredFeaturesMain: false,
        eventSummarization: false,
        generateQuery: false,
      },
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    systemSettings() {
      return this.$store.state.systemSettings
    },
    userSettings() {
      return this.$store.state.settings
    },
  },
  methods: {
    saveSettings() {
      ApiClient.saveUserSettings(this.settings)
        .then(() => this.$store.dispatch('updateUserSettings'))
        .catch((error) => {
          console.log(error)
        })
    },
    updateAiFeatures() {
      if (!this.settings.aiPoweredFeaturesMain) {
        this.settings.eventSummarization = false;
        this.settings.generateQuery = false;
      }
      this.saveSettings();
    },
  },
  mounted() {
    this.settings = { ...this.userSettings }

    // Set default values when a user don't have any settings saved.
    if (!this.settings || !Object.keys(this.settings).length) {
      this.settings = { ...DEFAULT_SETTINGS }
      this.saveSettings()
    } else {
      // Ensure default values for new settings are applied if user settings are older
      this.settings.aiPoweredFeaturesMain = this.settings.aiPoweredFeaturesMain !== undefined ? this.settings.aiPoweredFeaturesMain : DEFAULT_SETTINGS.aiPoweredFeaturesMain;
      this.settings.eventSummarization = this.settings.eventSummarization !== undefined ? this.settings.eventSummarization : DEFAULT_SETTINGS.eventSummarization;
      this.settings.generateQuery = this.settings.generateQuery !== undefined ? this.settings.generateQuery : DEFAULT_SETTINGS.generateQuery;
    }
  },
}
</script>