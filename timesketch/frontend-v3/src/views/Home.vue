<!--
Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
  <v-container fluid class="pa-0">
    <v-sheet class="pa-5" :color="theme.global.current.value.dark ? 'grey-darken-4' : 'grey-lighten-3'" min-height="200">
      <h2>Start new investigation</h2>
      <v-row no-gutters class="mt-5">
        <v-dialog v-model="createSketchDialog" width="500">
          <template v-slot:activator="{ props }">
            <v-btn variant="flat" size="small" class="mr-5" color="primary" v-bind="props"> Blank sketch </v-btn>
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
                <v-btn text @click="createSketchDialog = false"> Cancel </v-btn>
                <v-btn
                  :disabled="!sketchForm.name || sketchForm.name.length > 255"
                  @click="createSketch()"
                  color="primary"
                  text
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
</template>

<script>
import TsSketchList from "@/components/SketchList.vue";
import ApiClient from '../utils/RestApiClient.js'
import { useAppStore } from "@/stores/app";
import { useTheme } from 'vuetify'

export default {
  components: {
    TsSketchList,
  },
  setup() {
    const theme = useTheme();
    return { theme };
  },
  data() {
    return {
      sketchForm: {
        name: '',
      },
      appStore: useAppStore(),
      createSketchDialog: false,
      sketchNameRules: [
        (v) => !!v || 'Sketch name is required.',
        (v) => (v && v.length <= 255) || 'Sketch name is too long.',
      ],
    };
  },
  computed: {},
  methods: {
    clearFormData: function () {
      this.sketchForm.name = ''
    },
    createSketch: function () {
      ApiClient.createSketch(this.sketchForm)
        .then((response) => {
          let newSketchId = response.data.objects[0].id
          this.clearFormData()
          this.$router.push({ name: 'overview', params: { sketchId: newSketchId } })
        })
        .catch((e) => {})
    },

  },
};
</script>
