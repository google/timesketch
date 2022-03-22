<!--
Copyright 2021 Google Inc. All rights reserved.

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
  <v-card outlined>
    <!--
    <v-toolbar flat>

      <v-toolbar-title v-if="!activeQuestion.display_name" style="font-size: 1em">
        Investigative Questions</v-toolbar-title
      >
      <v-toolbar-title style="font-size: 1em"> {{ activeQuestion.display_name }}</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn v-on:click="addScenario">Add scenario</v-btn>
      <v-btn icon>
        <v-icon>mdi-view-dashboard</v-icon>
      </v-btn>
      <v-btn icon>
        <v-icon>mdi-dots-vertical</v-icon>
      </v-btn>
    </v-toolbar>
    -->

    <v-toolbar flat>
      <v-tabs v-model="tab" v-on:change="resetActiveQuestion()" show-arrows>
        <v-tab v-for="facet in scenario.facets" :key="facet.id">
          <!--
          <v-avatar size="28" class="mr-2">
            <img src="https://avatars.githubusercontent.com/u/316362?v=4" alt="Johan" />
          </v-avatar>
          -->
          {{ facet.display_name }}
        </v-tab>
      </v-tabs>

      <v-btn icon>
        <v-icon>mdi-plus</v-icon>
      </v-btn>
    </v-toolbar>

    <v-tabs-items v-model="tab">
      <v-tab-item :transition="false" v-for="facet in scenario.facets" :key="facet.id">
        <v-card flat class="mt-3">
          <v-row style="min-height: 200px">
            <v-col cols="4">
              <v-list>
                <v-list-item-group v-model="selectedItem" color="primary">
                  <v-list-item
                    v-for="question in facet.questions"
                    :key="question.id"
                    v-on:click="setActiveQuestion(question)"
                  >
                    <v-list-item-icon>
                      <v-icon color="green">mdi-checkbox-marked-circle-outline</v-icon>
                      <!--<v-icon>mdi-checkbox-blank-circle-outline</v-icon>-->
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title v-text="question.display_name"></v-list-item-title>
                    </v-list-item-content>
                  </v-list-item>
                </v-list-item-group>
              </v-list>
            </v-col>
            <v-divider vertical></v-divider>
            <v-col cols="8" v-if="activeQuestion.description">
              <v-card flat class="mt-2 mr-3">
                <v-alert dense text type="info">
                  {{ activeQuestion.description }}
                </v-alert>

                <li v-for="analyzer in activeQuestionSpec.analyzers" :key="analyzer">
                  {{ analyzer }}
                </li>
              </v-card>
            </v-col>
          </v-row>
        </v-card>
      </v-tab-item>
    </v-tabs-items>
  </v-card>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  props: [],
  data: function () {
    return {
      scenario: {},
      tab: '',
      activeQuestion: {},
      selectedItem: null,
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
  created() {
    ApiClient.getSketchScenarios(this.sketch.id)
      .then((response) => {
        this.scenario = response.data.objects[0][1]
      })
      .catch((e) => {})
  },
}
</script>
