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
    <v-main>
      <!-- Top horizontal toolbar -->
      <v-toolbar dense flat>
        <div v-if="isRootPage">
          <v-avatar class="mt-2 ml-n4">
            <router-link to="/">
              <v-img src="/dist/timesketch-color.png" max-height="25" max-width="25" contain></v-img>
            </router-link>
          </v-avatar>
          <span style="font-size: 1.2em">timesketch</span>
        </div>
        <v-spacer></v-spacer>
        <v-btn small depressed v-on:click="switchUI"> Use the old UI </v-btn>
        <v-btn v-if="!isRootPage" small depressed color="primary" class="ml-2">
          <v-icon small left>mdi-account-multiple-plus</v-icon>
          Share
        </v-btn>
        <v-avatar color="grey lighten-1" size="25" class="ml-3">
          <span class="white--text">{{ currentUser.charAt(0).toUpperCase() }}</span>
        </v-avatar>
        <v-menu v-if="!isRootPage" offset-y>
          <template v-slot:activator="{ on, attrs }">
            <v-avatar>
              <v-btn small icon v-bind="attrs" v-on="on">
                <v-icon>mdi-dots-vertical</v-icon>
              </v-btn>
            </v-avatar>
          </template>
          <v-card>
            <v-list>
              <v-list-item-group color="primary">
                <v-list-item v-on:click="toggleTheme">
                  <v-list-item-icon>
                    <v-icon>mdi-brightness-6</v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>Toggle theme</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-icon>
                    <v-icon>mdi-archive</v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>Archive sketch</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>

                <v-list-item>
                  <v-list-item-icon>
                    <v-icon>mdi-export</v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>Export sketch</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </v-list-item-group>
            </v-list>
          </v-card>
        </v-menu>
      </v-toolbar>
      <v-divider></v-divider>

      <!-- Main view -->
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
      mini: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    currentUser() {
      return this.$store.state.currentUser
    },
    isRootPage() {
      return Object.keys(this.sketch).length === 0
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
      if (isDark === 'true') {
        this.$vuetify.theme.dark = true
      } else {
        this.$vuetify.theme.dark = false
      }
    }
    this.$store.dispatch('resetState', this.sketchId)
  },
}
</script>

<style lang="scss"></style>
