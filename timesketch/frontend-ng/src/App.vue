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
  <v-app id="app">
    <v-app-bar app clipped-left flat :color="$vuetify.theme.dark ? '' : 'white'">
      <v-img src="/dist/timesketch-color.png" max-height="30" max-width="30" contain></v-img>
      <v-toolbar-title class="ml-3"> timesketch </v-toolbar-title>
      <span v-if="sketch.name" class="ml-6" style="margin-top: 5px">
        {{ sketch.name }}
      </span>
      <v-spacer></v-spacer>

      <v-btn small depressed v-on:click="switchUI"> Use the old UI </v-btn>

      <v-tooltip bottom>
        <template v-slot:activator="{ on, attrs }">
          <v-btn icon v-on:click="toggleTheme" v-bind="attrs" v-on="on">
            <v-icon>mdi-brightness-6</v-icon>
          </v-btn>
        </template>
        <span>Switch between light and dark theme</span>
      </v-tooltip>

      <v-avatar class="ml-3" color="orange" size="32">
        <span class="white--text">jb</span>
      </v-avatar>

      <template v-slot:extension>
        <v-tabs class="ml-2">
          <v-tab :to="{ name: 'Overview' }" exact-path><v-icon left small>mdi-cube-outline</v-icon> Overview</v-tab>
          <v-tab :to="{ name: 'Explore' }"><v-icon left small>mdi-magnify</v-icon> Explore </v-tab>
          <v-tab disabled><v-icon left small>mdi-lan</v-icon> Graph </v-tab>
          <v-tab disabled><v-icon left small>mdi-auto-fix</v-icon>Automation</v-tab>
          <v-tab disabled><v-icon left small>mdi-head-lightbulb</v-icon>Intelligence</v-tab>
        </v-tabs>
      </template>
    </v-app-bar>



    <v-main class="mx-4">
      <router-view></router-view>
    </v-main>

  </v-app>
</template>

<script>
export default {
  name: 'app',
  data() {
    return {
      drawer: true,
      mini: false
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  methods: {
    toggleTheme: function () {
      this.$vuetify.theme.dark = !this.$vuetify.theme.dark
      localStorage.setItem('isDarkTheme', this.$vuetify.theme.dark.toString())
    },
    switchUI: function () {
      window.location.href = window.location.href.replace('/v2/', '/')
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
<style lang="scss">
.v-toolbar__content,
.v-toolbar__extension {
  border-bottom: thin solid rgba(0, 0, 0, 0.12);
}
.v-tab {
  text-transform: none !important;
}
</style>
