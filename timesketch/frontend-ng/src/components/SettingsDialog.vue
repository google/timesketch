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
      <v-list-item>
        <v-list-item-action>
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <div v-on="isAnyFeatureAvailable ? {} : on" v-bind="attrs">
                <v-switch 
                  v-model="adjustedSettings.aiPoweredFeaturesMain" 
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
                  v-model="adjustedSettings.eventSummarization"
                  color="primary"
                  @change="saveSettings()"
                  :disabled="!adjustedSettings.aiPoweredFeaturesMain || !isFeatureAvailable('llm_summarize')"
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
                  v-model="adjustedSettings.generateQuery"
                  color="primary"
                  @change="saveSettings()"
                  :disabled="!adjustedSettings.aiPoweredFeaturesMain || !isFeatureAvailable('nl2q')"
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
      
      <v-list-item v-if="systemSettings.SEARCH_PROCESSING_TIMELINES">
        <v-list-item-action>
          <v-switch v-model="settings.showProcessingTimelineEvents" color="primary" @change="saveSettings()"></v-switch>
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
      return Object.values(this.llmFeatures).some(available => available === true);
    },
    adjustedSettings() {
      const adjusted = { ...this.settings };
      
      if (!this.isAnyFeatureAvailable) {
        adjusted.aiPoweredFeaturesMain = false;
      }
      
      if (!this.isFeatureAvailable('llm_summarize')) {
        adjusted.eventSummarization = false;
      }
      
      if (!this.isFeatureAvailable('nl2q')) {
        adjusted.generateQuery = false;
      }
      
      return adjusted;
    }
  },
  methods: {
    saveSettings() {
      // Use the adjusted settings which already have the availability constraints applied
      ApiClient.saveUserSettings(this.adjustedSettings)
        .then(() => {
          // Update local settings after saving
          this.settings = { ...this.adjustedSettings };
          return this.$store.dispatch('updateUserSettings');
        })
        .catch((error) => {
          console.log(error);
        });
    },
    updateAiFeatures() {
      if (!this.adjustedSettings.aiPoweredFeaturesMain) {
        this.settings.eventSummarization = false;
        this.settings.generateQuery = false;
      }
      this.saveSettings();
    },
    isFeatureAvailable(featureName) {
      return this.llmFeatures[featureName] === true;
    },
    syncSettingsWithAvailability() {
      // Update settings based on feature availability
      let needsUpdate = false;
      
      if (!this.isAnyFeatureAvailable && this.settings.aiPoweredFeaturesMain) {
        this.settings.aiPoweredFeaturesMain = false;
        needsUpdate = true;
      }
      
      if (!this.isFeatureAvailable('llm_summarize') && this.settings.eventSummarization) {
        this.settings.eventSummarization = false;
        needsUpdate = true;
      }
      
      if (!this.isFeatureAvailable('nl2q') && this.settings.generateQuery) {
        this.settings.generateQuery = false;
        needsUpdate = true;
      }
      
      if (needsUpdate) {
        this.saveSettings();
      }
    }
  },
  mounted() {
    this.settings = { ...this.userSettings }
    // Set default values when a user doesn't have any settings saved.
    if (!this.settings || !Object.keys(this.settings).length) {
      this.settings = { ...DEFAULT_SETTINGS }
      this.saveSettings()
    } else {
      // Ensure default values for new settings are applied if user settings are older
      this.settings.aiPoweredFeaturesMain = this.settings.aiPoweredFeaturesMain !== undefined ? this.settings.aiPoweredFeaturesMain : DEFAULT_SETTINGS.aiPoweredFeaturesMain;
      this.settings.eventSummarization = this.settings.eventSummarization !== undefined ? this.settings.eventSummarization : DEFAULT_SETTINGS.eventSummarization;
      this.settings.generateQuery = this.settings.generateQuery !== undefined ? this.settings.generateQuery : DEFAULT_SETTINGS.generateQuery;
      this.settings.showProcessingTimelineEvents = this.settings.showProcessingTimelineEvents !== undefined ? this.settings.showProcessingTimelineEvents : DEFAULT_SETTINGS.showProcessingTimelineEvents;
      
      this.$nextTick(() => {
        this.syncSettingsWithAvailability();
      });
    }
  },
}
</script>
