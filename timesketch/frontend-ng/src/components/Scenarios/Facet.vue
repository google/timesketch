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
      class="pa-3 pl-1"
      style="cursor: pointer"
      @click="toggleFacet()"
      :class="[$vuetify.theme.dark ? 'dark-hover' : 'light-hover']"
    >
      <v-col cols="1" class="pl-1">
        <v-icon v-if="!expanded">mdi-chevron-right</v-icon>
        <v-icon v-else>mdi-chevron-down</v-icon>
      </v-col>
      <v-col cols="10">
        <span style="font-size: 0.9em">
          <span v-if="notStarted || isActive"
            ><strong>{{ facet.display_name }}</strong></span
          >
          <span v-else>{{ facet.display_name }}</span>
        </span>
      </v-col>

      <v-col cols="1">
        <div class="ml-1">
          <small>{{ questionsWithConclusion.length }}/{{ facet.questions.length }} </small>
        </div>
      </v-col>
    </v-row>

    <v-expand-transition>
      <div v-show="expanded">
        <span
          @click="setActiveContext(question)"
          style="font-size: 0.9em"
          v-for="question in facet.questions"
          :key="question.id"
        >
          <ts-question :question="question"></ts-question>
        </span>
      </div>
    </v-expand-transition>
    <div v-show="expanded" class="mt-3"></div>
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
