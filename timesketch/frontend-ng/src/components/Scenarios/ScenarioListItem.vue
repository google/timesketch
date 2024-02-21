<!--
Copyright 2024 Google Inc. All rights reserved.

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
  <v-list-item @click="$emit('set-active-scenario', scenario)">
    <!-- Rename dialog -->
    <v-dialog v-model="renameDialog" max-width="500">
      <v-card class="pa-4">
        <v-form @submit.prevent="renameScenario()">
          <h3>Rename scenario</h3>
          <br />
          <v-text-field outlined dense autofocus v-model="newName" @focus="$event.target.select()"></v-text-field>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn text @click="renameDialog = false"> Cancel </v-btn>
            <v-btn color="primary" text @click="renameScenario()"> Save </v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>
    <v-list-item-content style="max-width: 300px">
      <v-list-item-title>
        {{ scenario.display_name }}
      </v-list-item-title>
    </v-list-item-content>
    <v-list-item-action>
      <v-menu offset-y :close-on-content-click="true">
        <template v-slot:activator="{ on, attrs }">
          <v-btn class="ml-1" small icon v-bind="attrs" v-on="on">
            <v-icon>mdi-dots-vertical</v-icon>
          </v-btn>
        </template>
        <v-card>
          <v-list dense>
            <v-list-item-group color="primary">
              <v-list-item @click.stop="renameDialog = true">
                <v-list-item-icon>
                  <v-icon small>mdi-pencil</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Rename</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              <v-list-item @click.stop="$emit('copy-scenario', scenario)">
                <v-list-item-icon>
                  <v-icon small>mdi-content-copy</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Make a copy</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              <v-list-item @click="$emit('set-scenario-status', 'deleted')">
                <v-list-item-icon>
                  <v-icon small>mdi-trash-can</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Move to trash</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </v-list-item-group>
          </v-list>
        </v-card>
      </v-menu>
    </v-list-item-action>
  </v-list-item>
</template>

<script>
import ApiClient from '../../utils/RestApiClient.js'

export default {
  props: {
    scenario: Object,
  },
  data() {
    return {
      renameDialog: false,
      newName: this.scenario.display_name,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  methods: {
    renameScenario: function () {
      this.renameDialog = false
      ApiClient.renameScenario(this.sketch.id, this.scenario.id, this.newName)
        .then((response) => {
          let updatedScenario = response.data.objects[0]
          this.$emit('rename-scenario', updatedScenario)
        })
        .catch((e) => {
          console.error(e)
        })
    },
  },
}
</script>
