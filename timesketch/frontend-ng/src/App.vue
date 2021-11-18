<!--
Copyright 2019 Google Inc. All rights reserved.

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
  <v-app id="app"
    >""
    <v-app-bar app outlined flat>
      <v-img src="/dist/timesketch-color.png" max-height="30" max-width="30" contain></v-img>
      <v-toolbar-title class="ml-3"> timesketch </v-toolbar-title>

      <v-spacer></v-spacer>

      <v-btn icon v-on:click="toggleTheme">
        <v-icon>mdi-brightness-6</v-icon>
      </v-btn>

      <v-avatar class="ml-3" color="orange" size="32">
        <span class="white--text">jb</span>
      </v-avatar>

      <!-- 
      <template v-slot:extension>
        <v-tabs>
          <v-tab>Overview</v-tab>
          <v-tab :to="{ name: 'Explore' }"> Explore </v-tab>
          <v-tab>Graph</v-tab>
          <v-tab>Aggregate</v-tab>
          <v-tab>Analyze</v-tab>
          <v-tab>Timelines</v-tab>
          <v-tab>Stories</v-tab>
        </v-tabs>
      </template>
    -->
    </v-app-bar>

    <v-main>
      <v-container fluid>
        <router-view></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
export default {
  name: 'app',
  methods: {
    toggleTheme: function () {
      this.$vuetify.theme.dark = !this.$vuetify.theme.dark
      localStorage.setItem('isDarkTheme', this.$vuetify.theme.dark.toString())
    },
  },
  mounted() {
    const isDark = localStorage.getItem('isDarkTheme')
    if (isDark) {
      if (isDark == 'true') {
        this.$vuetify.theme.dark = true
      } else {
        this.$vuetify.theme.dark = false
      }
    }
  },
}
</script>

<style src="vue-multiselect/dist/vue-multiselect.min.css"></style>
<style lang="scss"></style>
