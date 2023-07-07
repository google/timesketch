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
    <v-row
      no-gutters
      class="pa-3"
      style="cursor: pointer"
      @click="toggleFacet()"
      :class="
        $vuetify.theme.dark
          ? expanded
            ? 'dark-highlight'
            : 'dark-hover'
          : expanded
          ? 'light-highlight'
          : 'light-hover'
      "
    >
      <v-col cols="1" class="pl-1">
        <v-icon v-if="!expanded">mdi-chevron-right</v-icon>
        <v-icon v-else>mdi-chevron-down</v-icon>
      </v-col>

      <v-col cols="10" class="pl-1">
        <span style="font-size: 0.9em">
          {{ facet.display_name }}
        </span>
      </v-col>

      <v-col cols="1">
        <v-chip style="padding-left: 8px" x-small :color="isResolved ? 'success' : ''" :outlined="!isResolved">
          {{ questionsWithConclusion.length }}/{{ facet.questions.length }}
        </v-chip>
      </v-col>
    </v-row>

    <v-expand-transition>
      <div v-show="expanded">
        <span
          @click="setActiveContext(question)"
          style="font-size: 0.9em"
          v-for="(question, index) in facet.questions"
          :key="question.id"
        >
          <ts-question :question="question"></ts-question>
          <v-divider v-if="index != facet.questions.length - 1"></v-divider>
        </span>
      </div>
    </v-expand-transition>
    <div v-show="expanded"></div>
    <v-divider></v-divider>
  </div>
</template>

<script>
import TsQuestion from './Question'

export default {
  props: ['scenario', 'facet'],
  components: { TsQuestion },
  data: function () {
    return {
      expanded: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    questionsWithConclusion() {
      return this.facet.questions.filter((question) => question.conclusions.length)
    },
    isActive() {
      return (
        this.questionsWithConclusion.length > 0 && this.questionsWithConclusion.length < this.facet.questions.length
      )
    },
    isResolved() {
      return this.questionsWithConclusion.length === this.facet.questions.length
    },
    notStarted() {
      return this.questionsWithConclusion.length === 0
    },
  },
  methods: {
    toggleFacet: function () {
      if (!this.expanded) {
        this.setActiveContext()
      } else {
        if (this.$store.state.activeContext.facet != null) {
          if (this.facet.id === this.$store.state.activeContext.facet.id) {
            this.$store.dispatch('clearActiveContext')
          }
        }
      }
      this.expanded = !this.expanded
    },
    setActiveContext: function (question) {
      let payload = {
        scenario: this.scenario,
        facet: this.facet,
        question: question,
      }
      this.$store.dispatch('setActiveContext', payload)
    },
  },
  created() {},
}
</script>
