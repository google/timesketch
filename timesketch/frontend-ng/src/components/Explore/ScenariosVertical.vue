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
  <v-sheet class="ma-1">
    <v-expansion-panels accordion flat>
      <v-expansion-panel v-for="facet in scenario.facets" :key="facet.id">
        <v-expansion-panel-header>
          {{ facet.display_name }}
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-expansion-panels accordion flat>
            <v-expansion-panel v-for="question in facet.questions" :key="question.id">
              <v-expansion-panel-header>
                <v-list-item-title v-text="question.display_name"></v-list-item-title>
              </v-expansion-panel-header>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-sheet>
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
