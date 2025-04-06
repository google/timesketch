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
          <v-switch
            v-model="settings.showLeftPanel"
            color="primary"
            @change="saveSettings()"
          ></v-switch>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>Show side panel</v-list-item-title>
          <v-list-item-subtitle
            >Select if the side panel should be expanded or collapsed by default</v-list-item-subtitle
          >
        </v-list-item-content>
      </v-list-item>

      <!-- AI Powered Features Main Setting -->
      <v-list-item>
        <v-list-item-action>
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <div v-on="isAnyFeatureAvailable ? {} : on" v-bind="attrs">
                <v-switch
                  v-model="settings.aiPoweredFeaturesMain"
                  color="primary"
                  @change="updateAiFeatures"
                  :disabled="!isAnyFeatureAvailable"
                ></v-switch>
              </div>
            </template>
            <span>This feature requires an LLM provider to be configured. Please contact your administrator.</span>
          </v-tooltip>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>AI powered features (experimental)</v-list-item-title>
          <v-list-item-subtitle>Main switch to enable or disable all experimental AI features</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>

      <!-- Child Setting: Event Summarization -->
      <v-list-item>
        <v-list-item-action class="ml-8">
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <div v-on="isFeatureAvailable('llm_summarize') ? {} : on" v-bind="attrs">
                <v-switch
                  v-model="settings.eventSummarization"
                  color="primary"
                  @change="saveSettings()"
                  :disabled="!settings.aiPoweredFeaturesMain || !isFeatureAvailable('llm_summarize')"
                ></v-switch>
              </div>
            </template>
            <span>Event summarization requires an LLM provider to be configured. Please contact your administrator.</span>
          </v-tooltip>
        </v-list-item-action>
        <v-list-item-content class="ml-8">
          <v-list-item-title>Event summarization</v-list-item-title>
          <v-list-item-subtitle
            >Enable AI powered summarization of events</v-list-item-subtitle
          >
        </v-list-item-content>
      </v-list-item>

      <!-- Child Setting: AI Generated Queries -->
      <v-list-item>
        <v-list-item-action class="ml-8">
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <div v-on="isFeatureAvailable('nl2q') ? {} : on" v-bind="attrs">
                <v-switch
                  v-model="settings.generateQuery"
                  color="primary"
                  @change="saveSettings()"
                  :disabled="!settings.aiPoweredFeaturesMain || !isFeatureAvailable('nl2q')"
                ></v-switch>
              </div>
            </template>
            <span>AI query generation requires an LLM provider to be configured. Please contact your administrator.</span>
          </v-tooltip>
        </v-list-item-action>
        <v-list-item-content class="ml-8">
          <v-list-item-title>AI generated queries</v-list-item-title>
          <v-list-item-subtitle
            >Enable experimental AI query suggestions for DFIQ questions</v-list-item-subtitle
          >
        </v-list-item-content>
      </v-list-item>

      <!-- Setting: Searching processing timelines -->
      <v-list-item v-if="systemSettings.SEARCH_PROCESSING_TIMELINES">
        <v-list-item-action>
          <v-switch
            v-model="settings.showProcessingTimelineEvents"
            color="primary"
            @change="saveSettings()"
          ></v-switch>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>Include Processing Events</v-list-item-title>
          <v-list-item-subtitle
          >Allows queries to include events from timelines still being <strong>processed</strong>.</v-list-item-subtitle
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
  showProcessingTimelineEvents: false,
}
export default {
  data() {
    return {
      settings: {
        showLeftPanel: true,
        aiPoweredFeaturesMain: false,
        eventSummarization: false,
        generateQuery: false,
        showProcessingTimelineEvents: false,
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
    llmFeatures() {
      return this.systemSettings.LLM_FEATURES_AVAILABLE || {}
    },
    isAnyFeatureAvailable() {
      return Object.values(this.llmFeatures).some(available => available === true)
    },
  },
  methods: {
    saveSettings() {
      ApiClient.saveUserSettings(this.settings)
        .then(() => {
          return this.$store.dispatch('updateUserSettings')
        })
        .then(() => {
          this.settings = { ...this.userSettings }
        })
        .catch((error) => {
          console.log(error)
        })
    },
    updateAiFeatures() {
      if (!this.settings.aiPoweredFeaturesMain) {
        this.settings.eventSummarization = false
        this.settings.generateQuery = false
      }
      this.saveSettings()
    },
    isFeatureAvailable(featureName) {
      return this.llmFeatures[featureName] === true
    },
  },
  mounted() {
    // Set default settings if no user settings are defined.
    this.settings = { ...DEFAULT_SETTINGS, ...this.userSettings };
    this.saveSettings();
  },
}
</script>
