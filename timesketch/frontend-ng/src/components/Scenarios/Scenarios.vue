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
  <v-sheet v-if="scenario">
    <v-toolbar dense flat>
      <v-toolbar-title style="font-size: 1.1em">Compromise assessment</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon small>
        <v-icon small>mdi-chevron-left</v-icon>
      </v-btn>
    </v-toolbar>
    <!-- <v-btn @click="addScenario">Add scenario</v-btn> -->
    <v-sheet v-for="facet in scenario.facets" :key="facet.id">
      <ts-facets :facet="facet"></ts-facets>
    </v-sheet>
  </v-sheet>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsFacets from './Facets'

export default {
  props: [],
  components: { TsFacets },
  data: function () {
    return {
      scenario: { facets: [] },
      tab: '',
      activeQuestion: {},
      selectedItem: null,
      expandedFacets: [],
      dessertHeaders: [
        { text: '', value: 'data-table-expand' },
        {
          text: '',
          align: 'start',
          sortable: false,
          value: 'display_name',
        },
        { text: '', value: 'status' },
      ],
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
