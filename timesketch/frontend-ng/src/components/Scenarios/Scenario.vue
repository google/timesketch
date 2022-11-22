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
      <slot></slot>
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
}
</script>

<style scoped lang="scss"></style>
