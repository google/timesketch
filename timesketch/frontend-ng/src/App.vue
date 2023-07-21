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
    <!-- Global snackbar -->
    <v-snackbar v-model="snackbar.active" :timeout="snackbar.timeout" :color="snackbar.color" top>
      {{ snackbar.message }}
      <template v-slot:action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbar.active = false"> Close </v-btn>
      </template>
    </v-snackbar>

    <v-main class="notransition">
      <!-- Main view -->
      <router-view></router-view>
    </v-main>
  </v-app>
</template>

<script>
import EventBus from './main'

export default {
  name: 'app',
  data() {
    return {}
  },
  computed: {
    snackbar() {
      return this.$store.state.snackbar
    },
  },
  methods: {
    setErrorSnackBar: function (message) {
      const snackbar = {
        message: message,
        color: 'error',
        timeout: 7000,
      }
      this.$store.dispatch('setSnackBar', snackbar)
    },
  },
  mounted() {
    // Listen on errors from REST API calls
    EventBus.$on('errorSnackBar', this.setErrorSnackBar)

    const isDark = localStorage.getItem('isDarkTheme')
    if (isDark) {
      if (isDark === 'true') {
        this.$vuetify.theme.dark = true
      } else {
        this.$vuetify.theme.dark = false
      }
    }
    let element = document.body
    element.dataset.theme = this.$vuetify.theme.dark ? 'dark' : 'light'
  },
  beforeDestroy() {
    EventBus.$off('errorSnackBar')
  },
}
</script>

<style lang="scss"></style>
