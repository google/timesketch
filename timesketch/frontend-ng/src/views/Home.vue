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
    <v-container fluid pa-0>
      <v-sheet class="pa-5" :color="$vuetify.theme.dark ? 'grey darken-4' : 'grey lighten-3'" min-height="200">
        <h2>Start new investigation</h2>
        <v-row no-gutters class="mt-5">
          <v-dialog width="500">
            <template v-slot:activator="{ on, attrs }">
              <v-btn depressed small class="mr-5" color="primary" v-bind="attrs" v-on="on"> Blank sketch </v-btn>
            </template>
            <v-card class="pa-3">
              <h3>New sketch</h3>
              <br />
              <v-text-field v-model="sketchForm.name" outlined dense placeholder="Name your sketch"> </v-text-field>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn :disabled="!sketchForm.name" @click="createSketch()" color="primary" text> Create </v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
          <v-divider vertical class="mr-5"></v-divider>
          <v-btn v-for="scenario in scenarioTemplates" :key="scenario.short_name" depressed small outlined class="mr-5">
            {{ scenario.display_name }}
          </v-btn>
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
      scenarioTemplates: [],
    }
  },
  methods: {
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
    ApiClient.getScenarios()
      .then((response) => {
        this.scenarioTemplates = response.data['objects']
      })
      .catch((e) => {})
  },
}
</script>
<style lang="scss"></style>
