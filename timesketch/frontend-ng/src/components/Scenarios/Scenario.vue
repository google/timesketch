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
  <div v-if="iconOnly" class="pa-4" style="cursor: pointer" @click="$emit('toggleDrawer')">
    <v-icon start>mdi-clipboard-check-outline</v-icon>
    <div style="height: 1px"></div>
  </div>

  <div v-else>
    <v-row
      no-gutters
      style="cursor: pointer"
      @click="expanded = !expanded"
      class="pa-4"
      flat
      :class="
        this.$vuetify.theme.dark
          ? expanded
            ? 'dark-highlight'
            : 'dark-hover'
          : expanded
          ? 'light-highlight'
          : 'light-hover'
      "
    >
      <v-col cols="11">
        <v-icon start>mdi-clipboard-check-outline</v-icon>
        <span>{{ scenario.display_name }}</span>
      </v-col>
      <v-col cols="1">
        <!-- Rename dialog -->
        <v-dialog v-model="renameDialog" max-width="500">
          <v-card class="pa-4">
            <v-form @submit.prevent="renameScenario()">
              <h3>Rename scenario</h3>
              <br />
              <v-text-field variant="outlined" density="compact" autofocus v-model="newName" @focus="$event.target.select()"></v-text-field>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn variant="text" @click="renameDialog = false"> Cancel </v-btn>
                <v-btn color="primary" variant="text" @click="renameScenario()"> Save </v-btn>
              </v-card-actions>
            </v-form>
          </v-card>
        </v-dialog>
        <v-menu offset-y :close-on-content-click="true">
          <template v-slot:activator="{ props }">
            <v-btn v-bind="props" class="ml-1" size="small" icon >
              <v-icon>mdi-dots-vertical</v-icon>
            </v-btn>
          </template>
          <v-card>
            <v-list density="compact">
              <v-list-item @click="copyScenario(scenario.dfiq_identifier)">
                <v-list-item>
                  <v-icon size="small">mdi-content-copy</v-icon>
                </v-list-item>

                  <v-list-item-title>Make a copy</v-list-item-title>

              </v-list-item>

              <v-list-item @click.stop="renameDialog = true">
                <v-list-item>
                  <v-icon size="small">mdi-pencil</v-icon>
                </v-list-item>

                  <v-list-item-title>Rename</v-list-item-title>

              </v-list-item>
              <v-list-item v-if="is_hidden" @click="setStatus('active')">
                <v-list-item>
                  <v-icon size="small">mdi-eye</v-icon>
                </v-list-item>

                  <v-list-item-title>Reactivate</v-list-item-title>

              </v-list-item>
              <v-list-item v-else @click="setStatus('hidden')">
                <v-list-item>
                  <v-icon size="small">mdi-eye-off</v-icon>
                </v-list-item>

                  <v-list-item-title>Hide from list</v-list-item-title>

              </v-list-item>
            </v-list>
          </v-card>
        </v-menu>
      </v-col>
    </v-row>

    <v-expand-transition v-if="scenario.facets.length">
      <div v-if="expanded">
        <v-divider></v-divider>
        <div v-for="facet in scenario.facets" :key="facet.id">
          <ts-facet :scenario="scenario" :facet="facet"></ts-facet>
        </div>
      </div>
    </v-expand-transition>
    <v-divider v-if="!expanded"></v-divider>
    <br v-if="expanded" />
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient.js'
import TsFacet from './Facet.vue'

export default {
  props: ['scenario', 'iconOnly'],
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
    is_hidden() {
      if (!this.scenario.status.length) {
        return false
      }
      return this.scenario.status[0].status === 'hidden'
    },
  },
  methods: {
    renameScenario: function () {
      this.renameDialog = false
      ApiClient.renameScenario(this.sketch.id, this.scenario.id, this.newName)
        .then((response) => {
          this.$store.dispatch('updateScenarios', this.sketch.id)
        })
        .catch((e) => {})
    },
    copyScenario: function (scenarioId) {
      const displayName = 'Copy of ' + this.scenario.display_name
      ApiClient.addScenario(this.sketch.id, scenarioId, displayName)
        .then((response) => {
          this.$store.dispatch('updateScenarios', this.sketch.id)
        })
        .catch((e) => {})
    },
    setStatus: function (status) {
      ApiClient.setScenarioStatus(this.sketch.id, this.scenario.id, status)
        .then((response) => {
          this.$store.dispatch('updateScenarios', this.sketch.id)
        })
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
