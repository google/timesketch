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
  <v-dialog :value="dialog" @input="$emit('input', $event)" max-width="500px" persistent>
    <v-card>
      <div class="pa-3">
        <h3>Investigative Scenarios</h3>

        <v-select
          v-model="selectedScenario"
          :items="scenarioTemplates"
          item-text="display_name"
          return-object
          label="Select a scenario"
          outlined
          class="mt-3"
        ></v-select>
        <div v-if="selectedScenario">
          {{ selectedScenario.description }}
        </div>
      </div>
      <v-divider></v-divider>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click="closeDialog" color="primary" text> Close </v-btn>
        <v-btn :disabled="!selectedScenario" @click="addScenario(selectedScenario.short_name)" color="primary" text>
          Add
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  props: {
    dialog: Boolean,
  },
  data() {
    return {
      selectedScenario: null,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    scenarioTemplates() {
      return this.$store.state.scenarioTemplates
    },
  },
  methods: {
    closeDialog() {
      this.selectedScenario = null
      this.$emit('close-dialog')
    },
    addScenario: function (scenario) {
      this.closeDialog()
      ApiClient.addScenario(this.sketch.id, scenario)
        .then((response) => {
          this.$store.dispatch('updateScenarios', this.sketch.id)
        })
        .catch((e) => {})
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
