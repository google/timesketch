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
  <div v-if="scenario">
    <v-toolbar dense flat>
      <v-toolbar-title v-if="showPanel" style="font-size: 1em">Compromise assessment</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-icon v-if="showPanel" @click="$emit('togglePanel')">mdi-chevron-left</v-icon>
      <v-icon v-else @click="$emit('togglePanel')" style="margin-left: -5px">mdi-chevron-right</v-icon>
    </v-toolbar>
    <!-- <v-btn @click="addScenario">Add scenario</v-btn> -->
    <div v-show="showPanel">
      <div v-for="facet in scenario.facets" :key="facet.id">
        <ts-facet :facet="facet"></ts-facet>
      </div>
      <v-btn small text color="primary" class="ml-1 mt-3">+ Facet</v-btn>
    </div>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsFacet from './Facet'

export default {
  props: ['showPanel'],
  components: { TsFacet },
  data: function () {
    return {
      scenario: { facets: [] },
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
        this.scenario = response.data.objects[0][0]
      })
      .catch((e) => {})
  },
}
</script>

<style scoped lang="scss"></style>
