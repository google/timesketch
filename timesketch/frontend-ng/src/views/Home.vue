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
  <div>
    <!-- Top horizontal toolbar -->
    <v-toolbar flat color="transparent">
      <v-avatar class="mt-2 ml-n3">
        <router-link to="/">
          <v-img src="/dist/timesketch-color.png" max-height="25" max-width="25" contain></v-img>
        </router-link>
      </v-avatar>
      <span style="font-size: 1.2em">timesketch</span>

      <v-spacer></v-spacer>
      <v-btn small depressed v-on:click="switchUI"> Use the old UI </v-btn>
      <v-avatar color="grey lighten-1" size="25" class="ml-3">
        <span class="white--text">{{ currentUser | initialLetter }}</span>
      </v-avatar>
      <v-menu offset-y>
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

              <a href="/logout/" style="text-decoration: none; color: inherit">
                <v-list-item>
                  <v-list-item-icon>
                    <v-icon>mdi-logout</v-icon>
                  </v-list-item-icon>

                  <v-list-item-content>
                    <v-list-item-title>Logout</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </a>
            </v-list-item-group>
          </v-list>
        </v-card>
      </v-menu>
    </v-toolbar>

    <v-container fluid pa-0>
      <v-sheet class="pa-5" :color="$vuetify.theme.dark ? 'grey darken-4' : 'grey lighten-3'" min-height="200">
        <h2>Start new investigation</h2>
        <v-row no-gutters class="mt-5">
          <v-dialog v-model="createSketchDialog" width="500">
            <template v-slot:activator="{ on, attrs }">
              <v-btn depressed small class="mr-5" color="primary" v-bind="attrs" v-on="on"> Blank sketch </v-btn>
            </template>
            <v-card class="pa-4">
              <h3>New sketch</h3>
              <br />
              <v-form @submit.prevent="createSketch()">
                <v-text-field v-model="sketchForm.name" outlined dense placeholder="Name your sketch" autofocus>
                </v-text-field>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn text @click="createSketchDialog = false"> Cancel </v-btn>
                  <v-btn :disabled="!sketchForm.name" @click="createSketch()" color="primary" text> Create </v-btn>
                </v-card-actions>
              </v-form>
            </v-card>
          </v-dialog>
        </v-row>
      </v-sheet>
      <div class="pa-5">
        <h2>Your recent work</h2>
        <ts-sketch-list></ts-sketch-list>
      </div>
    </v-container>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsSketchList from '../components/SketchList'

export default {
  components: { TsSketchList },
  data() {
    return {
      sketchForm: {
        name: '',
      },
      createSketchDialog: false,
      scenarioTemplates: [],
    }
  },
  computed: {
    currentUser() {
      return this.$store.state.currentUser
    },
  },
  methods: {
    toggleTheme: function () {
      this.$vuetify.theme.dark = !this.$vuetify.theme.dark
      localStorage.setItem('isDarkTheme', this.$vuetify.theme.dark.toString())
    },
    switchUI: function () {
      window.location.href = '/legacy/'
    },
    clearFormData: function () {
      this.sketchForm.name = ''
    },
    createSketch: function () {
      ApiClient.createSketch(this.sketchForm)
        .then((response) => {
          let newSketchId = response.data.objects[0].id
          this.clearFormData()
          this.$router.push({ name: 'Overview', params: { sketchId: newSketchId } })
        })
        .catch((e) => {})
    },
  },
  created: function () {
    this.$store.dispatch('resetState')
    document.title = 'Timesketch'
    ApiClient.getScenarioTemplates()
      .then((response) => {
        this.scenarioTemplates = response.data['objects']
      })
      .catch((e) => {})
  },
}
</script>
<style lang="scss"></style>
