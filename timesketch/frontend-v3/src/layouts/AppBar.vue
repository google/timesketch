<!--
Copyright 2024 Google LLC

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
  <v-toolbar flat class="pr-4" color="transparent">
    <v-app-bar-title class="ml-n1">
      <span>timesketch</span>
    </v-app-bar-title>
    <template v-slot:prepend>
      <v-img
        src="/assets/timesketch-color.png"
        width="25"
        height="25"
        class="ml-4 mr-3"
      >
      </v-img>
    </template>
    <template v-slot:append>
      <v-avatar color="grey lighten-1" size="25" class="ml-3">
        <span class="white--text">{{ $filters.initialLetter(currentUser) }}</span>
      </v-avatar>
      <v-menu offset-y>
        <template v-slot:activator="{ props }">
          <v-btn small icon v-bind="props">
            <v-icon title="Timesketch Options">mdi-dots-vertical</v-icon>
          </v-btn>
        </template>
          <v-list>
            <v-list-item
              prepend-icon="mdi-brightness-6"
              v-on:click="toggleTheme"
            >
              <v-list-item-title>Toggle theme</v-list-item-title>
            </v-list-item>
            <v-list-item
              href="/legacy/"
              prepend-icon="mdi-view-dashboard-outline"
            >
              <v-list-item-title>Use the old UI</v-list-item-title>
            </v-list-item>
            <v-list-item
              href="/logout/"
              prepend-icon="mdi-logout"
            >
              <v-list-item-title>Logout</v-list-item-title>
            </v-list-item>
          </v-list>
      </v-menu>
    </template>
  </v-toolbar>
  <v-divider></v-divider>
</template>

<script>
import ApiClient from '../utils/RestApiClient.js'
import { useTheme } from 'vuetify'
import { useAppStore } from "@/stores/app";

export default {
  setup() {
    const theme = useTheme();
    return { theme };
  },
  data() {
    return {
      appStore: useAppStore(),
    };
  },
  computed: {
    currentUser() {
      return this.appStore.currentUser;
    }
  },
  methods: {
    toggleTheme: function () {
      this.theme.global.name.value = this.theme.global.current.value.dark ? 'light' : 'dark';
    },
  },
  created: function () {
    this.appStore.resetState();
  },
};
</script>
