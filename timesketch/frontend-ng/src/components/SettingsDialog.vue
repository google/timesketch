<!--
Copyright 2024 Google Inc. All rights reserved.

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
    </v-list>
  </v-card>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

const DEFAULT_SETTINGS = {
  showLeftPanel: true,
}

export default {
  data() {
    return {
      settings: null,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
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
