<!--
Copyright 2022 Google Inc. All rights reserved.

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
    <v-row no-gutters class="pa-4" flat :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
      <span style="cursor: pointer" @click="expanded = !expanded"
        ><v-icon left>mdi-clipboard-check-outline</v-icon> {{ scenario.display_name }}</span
      >
      <v-spacer></v-spacer>
      <!-- Rename dialog -->
      <v-dialog v-model="renameDialog" max-width="500">
        <v-card>
          <v-card-title class="text-h5"> Rename scenario </v-card-title>
          <v-card-text>
            Use a custom name for the scenario.
            <v-text-field v-model="newName"></v-text-field>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" text @click="renameDialog = false"> Cancel </v-btn>
            <v-btn color="primary" text @click="rename()"> Save </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      <v-menu offset-y :close-on-content-click="true">
        <template v-slot:activator="{ on, attrs }">
          <v-btn small icon v-bind="attrs" v-on="on">
            <v-icon>mdi-dots-vertical</v-icon>
          </v-btn>
        </template>
        <v-card>
          <v-list>
            <v-list-item-group color="primary">
              <v-list-item @click="addScenarioDialog">
                <v-list-item-icon>
                  <v-icon>mdi-content-copy</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Make a copy</v-list-item-title>
                </v-list-item-content>
              </v-list-item>

              <v-list-item @click.stop="renameDialog = true">
                <v-list-item-icon>
                  <v-icon>mdi-pencil</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Rename</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </v-list-item-group>
          </v-list>
        </v-card>
      </v-menu>
    </v-row>

    <v-expand-transition v-if="scenario.facets.length">
      <div v-show="expanded">
        <div v-for="facet in scenario.facets" :key="facet.id">
          <ts-facet :scenario="scenario" :facet="facet"></ts-facet>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsFacet from './Facet'

export default {
  props: ['scenario', 'minimizePanel'],
  components: { TsFacet },
  data: function () {
    return {
      activeQuestion: {},
      selectedItem: null,
      expanded: false,
      renameDialog: false,
      addScenarioDialog: false,
      newName: this.scenario.display_name,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    activeQuestionSpec() {
      return JSON.parse(this.activeQuestion.spec_json)
    },
  },
  methods: {
    rename: function () {
      this.renameDialog = false
      ApiClient.renameScenario(this.sketch.id, this.scenario.id, this.newName)
        .then((response) => {
          this.$store.dispatch('updateScenarios', this.sketch.id)
        })
        .catch((e) => {})
    },
    addScenario: function () {
      ApiClient.addScenario(this.sketch.id, 'compromise_assessment')
        .then((response) => {})
        .catch((e) => {})
    },
    setActiveQuestion: function (question) {
      this.activeQuestion = question
    },
    resetActiveQuestion: function () {
      this.selectedItem = null
      this.activeQuestion = {}
    },
  },
}
</script>

<style scoped lang="scss"></style>
