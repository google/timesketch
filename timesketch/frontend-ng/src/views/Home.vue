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
    <v-toolbar flat color="transparent" class="pl-3 pr-3">
      <router-link to="/">
        <v-img src="/dist/timesketch-color.png" class="mx-2" height="25" width="25" contain></v-img>
      </router-link>
      <span style="font-size: 1.2em">timesketch</span>

      <v-spacer></v-spacer>
      <v-avatar color="grey-lighten-1" size="25" class="ml-3">
        <span class="text-white">{{ this.$filters.initialLetter(currentUser) }}</span>
      </v-avatar>
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn v-bind="props" class="ml-1" icon="mdi-dots-vertical" density="compact" size="large" title="Timesketch Options"></v-btn>
        </template>
        <v-card>
          <v-list>
            <v-list-item v-on:click="toggleTheme">
              <v-list-item>
                <v-icon>mdi-brightness-6</v-icon>
              </v-list-item>

                <v-list-item-title>Toggle theme</v-list-item-title>

            </v-list-item>
            <v-list-item v-on:click="switchUI">
              <v-list-item>
                <v-icon>mdi-view-dashboard-outline</v-icon>
              </v-list-item>

                <v-list-item-title>Use the old UI</v-list-item-title>

            </v-list-item>

            <a href="/logout/" style="text-decoration: none; color: inherit">
              <v-list-item>
                <v-list-item>
                  <v-icon>mdi-logout</v-icon>
                </v-list-item>


                  <v-list-item-title>Logout</v-list-item-title>

              </v-list-item>
            </a>
          </v-list>
        </v-card>
      </v-menu>
    </v-toolbar>

    <!-- Main view -->
    <v-main class="notransition">
      <v-container fluid class="pa-0">
        <v-sheet class="pa-5" :color="this.$vuetify.theme.dark ? 'grey-darken-4' : 'grey-lighten-3'" min-height="200">
          <h2>Start new investigation</h2>
          <v-row no-gutters class="mt-5">
            <v-dialog v-model="createSketchDialog" width="500">
              <template v-slot:activator="{ props }">
                <v-btn v-bind="props" variant="flat" size="small" class="mr-5" color="primary"> Blank sketch </v-btn>
              </template>
              <v-card class="pa-4">
                <h3>New sketch</h3>
                <br />
                <v-form @submit.prevent="createSketch()">
                  <v-text-field
                    v-model="sketchForm.name"
                    variant="outlined"
                    density="compact"
                    placeholder="Name your sketch"
                    autofocus
                    clearable
                    :rules="sketchNameRules"
                  >
                  </v-text-field>
                  <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn variant="text" @click="createSketchDialog = false"> Cancel </v-btn>
                    <v-btn
                      :disabled="!sketchForm.name || sketchForm.name.length > 255"
                      @click="createSketch()"
                      color="primary"
                      variant="text"
                    >
                      Create
                    </v-btn>
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
    </v-main>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient.js'
import TsSketchList from '../components/SketchList.vue'

export default {
  components: { TsSketchList },
  data() {
    return {
      sketchForm: {
        name: '',
      },
      createSketchDialog: false,
      scenarioTemplates: [],
      sketchNameRules: [
        (v) => !!v || 'Sketch name is required.',
        (v) => (v && v.length <= 255) || 'Sketch name is too long.',
      ],
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
          const newSketchId = response.data.objects[0].id
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
        this.scenarioTemplates = response.data.objects
      })
      .catch((e) => {})
  },
}
</script>
<style lang="scss"></style>
