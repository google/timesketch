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
    <v-navigation-drawer v-if="!isRootPage" v-model="drawer" permanent app mini-variant class="pl-1">
      <v-avatar class="mb-2 mt-3">
        <router-link to="/">
          <v-img src="/dist/timesketch-color.png" max-height="30" max-width="30" contain></v-img>
        </router-link>
      </v-avatar>

      <v-tooltip right>
        <template v-slot:activator="{ on, attrs }">
          <v-avatar>
            <v-btn :to="{ name: 'Overview' }" exact-path icon v-bind="attrs" v-on="on">
              <v-icon>mdi-home-outline</v-icon>
            </v-btn>
          </v-avatar>
        </template>
        <span>Overview</span>
      </v-tooltip>

      <v-tooltip right>
        <template v-slot:activator="{ on, attrs }">
          <v-avatar>
            <v-btn :to="{ name: 'Explore' }" icon v-bind="attrs" v-on="on">
              <v-icon>mdi-magnify</v-icon>
            </v-btn>
          </v-avatar>
        </template>
        <span>Search</span>
      </v-tooltip>

      <v-tooltip right>
        <template v-slot:activator="{ on, attrs }">
          <v-avatar>
            <v-btn disabled icon v-bind="attrs" v-on="on">
              <v-icon>mdi-graph-outline</v-icon>
            </v-btn>
          </v-avatar>
        </template>
        <span>Graph</span>
      </v-tooltip>

      <v-avatar>
        <v-btn disabled icon>
          <v-icon>mdi-auto-fix</v-icon>
        </v-btn>
      </v-avatar>

      <v-avatar>
        <v-btn disabled icon>
          <v-icon>mdi-head-lightbulb-outline</v-icon>
        </v-btn>
      </v-avatar>
    </v-navigation-drawer>

    <v-main>
      <v-toolbar flat style="background: transparent" class="ml-2">
        <div v-if="isRootPage">
          <v-avatar>
            <v-img src="/dist/timesketch-color.png" max-height="40" max-width="40" contain></v-img>
          </v-avatar>
          <span style="font-size: 1.4em">timesketch</span>
        </div>

        <span style="font-size: 1.2em">{{ sketch.name }}</span>
        <v-spacer></v-spacer>
        <v-btn small depressed v-on:click="switchUI"> Use the old UI </v-btn>
        <v-tooltip right>
          <template v-slot:activator="{ on, attrs }">
            <v-avatar>
              <v-btn icon v-on:click="toggleTheme" v-bind="attrs" v-on="on">
                <v-icon>mdi-brightness-6</v-icon>
              </v-btn>
            </v-avatar>
          </template>
          <span>Switch between light and dark theme</span>
        </v-tooltip>
      </v-toolbar>

      <div class="mx-3 mt-n3">
        <router-view></router-view>
      </div>
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
  created() {
    console.log('app created')
  },
  mounted() {
    console.log('app mounted')
    const isDark = localStorage.getItem('isDarkTheme')
    if (isDark) {
      if (isDark === 'true') {
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
.v-tab {
  text-transform: none !important;
}
</style>
