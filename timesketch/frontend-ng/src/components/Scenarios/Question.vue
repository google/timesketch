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
      class="pa-2 pl-5"
      style="cursor: pointer; font-size: 0.9em"
      @click="expanded = !expanded"
      :class="
        $vuetify.theme.dark
          ? expanded
            ? 'dark-highlight-selected'
            : 'dark-hover'
          : expanded
          ? 'light-highlight-selected'
          : 'light-hover'
      "
    >
      <span v-if="expanded"
        ><strong>{{ question.display_name }}</strong></span
      >
      <span v-else>{{ question.display_name }}</span>
    </v-row>

    <v-expand-transition>
      <div
        v-show="expanded"
        :class="
          $vuetify.theme.dark
            ? expanded
              ? 'dark-highlight'
              : 'dark-hover'
            : expanded
            ? 'light-highlight'
            : 'light-hover'
        "
        class="pb-1"
      >
        <!-- Query suggestions -->
        <div class="pt-2 pl-5">
          <div v-if="searchTemplates.length || opensearchQueries.length">
            <small>Suggested queries</small>
            <v-chip-group column active-class="primary">
              <ts-search-chip
                v-for="searchtemplate in searchTemplates"
                :key="searchtemplate.id"
                :searchchip="searchtemplate"
              ></ts-search-chip>
              <ts-search-chip
                v-for="opensearchQuery in opensearchQueries"
                :key="opensearchQuery.value"
                :searchchip="opensearchQuery"
              ></ts-search-chip>
            </v-chip-group>
          </div>
          <div v-else><small>No suggested queries available</small></div>
        </div>

        <!-- Conclusions -->
        <div class="mb-3 pl-5">
          <v-sheet outlined rounded class="mt-2 mr-3" v-for="conclusion in question.conclusions" :key="conclusion.id">
            <ts-question-conclusion :question="question" :conclusion="conclusion"></ts-question-conclusion>
          </v-sheet>
        </div>

        <!-- Add new conclusion -->
        <div v-if="!currentUserConclusion" style="font-size: 0.9em" class="pb-4 mr-3 pl-5">
          <v-btn x-small text color="primary" @click="addConclusion = !addConclusion">
            <v-icon x-small>mdi-plus</v-icon>
            Add conclusion
          </v-btn>
          <v-textarea
            v-if="addConclusion"
            v-model="conclusionText"
            class="mt-3"
            outlined
            flat
            hide-details
            auto-grow
            rows="1"
            placeholder="Add your conclusion..."
            style="font-size: 0.9em"
          >
            <template v-slot:prepend-inner>
              <v-avatar color="grey" class="mt-n2 mr-2" size="28">
                <span class="white--text">{{ currentUser | initialLetter }}</span>
              </v-avatar>
            </template>
          </v-textarea>

          <v-card-actions v-if="addConclusion" class="pr-0">
            <v-spacer></v-spacer>
            <v-btn
              small
              text
              @click="
                conclusionText = ''
                addConclusion = false
              "
            >
              Cancel
            </v-btn>
            <v-btn small text color="primary" @click="createConclusion()" :disabled="!conclusionText"> Save </v-btn>
          </v-card-actions>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsSearchChip from './SearchChip'
import TsQuestionConclusion from './QuestionConclusion'

export default {
  props: ['question'],
  components: {
    TsSearchChip,
    TsQuestionConclusion,
  },
  data: function () {
    return {
      expanded: false,
      fullDescription: false,
      conclusionText: '',
      addConclusion: false,
      opensearchQueries: [],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    currentUser() {
      return this.$store.state.currentUser
    },
    searchTemplates() {
      return this.question.approaches.map((approach) => approach.search_templates).flat()
    },
    currentUserConclusion() {
      return this.question.conclusions.filter((conclusion) => conclusion.user.username === this.currentUser).length
    },
  },
  methods: {
    createConclusion() {
      ApiClient.createQuestionConclusion(this.sketch.id, this.question.id, this.conclusionText)
        .then((response) => {
          this.conclusionText = ''
          this.$store.dispatch('updateScenarios', this.sketch.id)
        })
        .catch((e) => {})
    },
    getSuggestedQueries() {
      let analyses = this.question.approaches
        .map((approach) => JSON.parse(approach.spec_json))
        .map((approach) => approach._view.processors)
        .map((processor) => processor[0].analysis.timesketch)
        .flat()
      this.opensearchQueries = analyses.filter((analysis) => analysis.type === 'opensearch-query')
    },
  },
  watch: {
    expanded: function (isExpanded) {
      if (!isExpanded) return
      if (this.opensearchQueries.length) return
      this.getSuggestedQueries()
    },
  },
}
</script>

<style scoped lang="scss">
.description-ellipsis {
  width: 500px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.dark-bg {
  background-color: #303030;
}
.light-bg {
  background-color: #f6f6f6;
}
</style>
