<!--
Copyright 2023 Google Inc. All rights reserved.

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
  <v-card
    v-if="activeContext.question"
    class="mx-3 pb-1 mb-3 mt-1"
    outlined
    color="#FAFAFA"
    style="border: 1px solid #d6d6d6"
  >
    <v-toolbar flat dense style="background-color: transparent">
      <v-btn v-if="activeContext.question.description" small icon @click="expanded = !expanded" class="mr-1">
        <v-icon v-if="expanded">mdi-chevron-up</v-icon>
        <v-icon v-else>mdi-chevron-down</v-icon>
      </v-btn>

      <strong>
        {{ activeContext.question.display_name }}
        <small>
          <a :href="getDfiqQuestionUrl(activeContext.question.dfiq_identifier)" target="_blank" rel="noreferrer"
            >({{ activeContext.question.dfiq_identifier }})</a
          >
        </small>
      </strong>

      <v-spacer></v-spacer>

      <v-btn small icon @click="$store.dispatch('clearActiveContext')" class="mr-1">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-toolbar>
    <v-divider v-show="expanded"></v-divider>

    <v-expand-transition>
      <div v-show="expanded">
        <div v-if="activeContext.question.description">
          <div
            class="pa-4 markdown-body"
            style="background-color: transparent"
            v-html="toHtml(activeContext.question.description)"
          ></div>
        </div>

        <!--Suggested queries-->
        <div v-if="opensearchQueries.length" class="px-4 pb-4">
          <strong style="font-size: 0.9em">Suggested queries</strong>
          <ts-search-chip
            v-for="opensearchQuery in opensearchQueries"
            :key="opensearchQuery.value"
            :searchchip="opensearchQuery"
            type="link"
          ></ts-search-chip>
        </div>

        <!--Approaches-->
        <div v-if="activeContext.question.approaches.length">
          <div class="px-4 pb-4">
            <v-btn depressed rounded small color="#EDEDED" @click="showApproaches = !showApproaches">
              <span v-if="!showApproaches">Show {{ activeContext.question.approaches.length }} approaches</span>
              <span v-else>Hide {{ activeContext.question.approaches.length }} approaches</span>
            </v-btn>
          </div>
          <v-expand-transition>
            <div v-if="showApproaches">
              <v-divider></v-divider>
              <v-expansion-panels flat accordion hover>
                <v-expansion-panel
                  v-for="(approach, index) in activeContext.question.approaches"
                  :key="approach.display_name"
                >
                  <v-expansion-panel-header>
                    <span>{{ approach.display_name }}</span>
                  </v-expansion-panel-header>
                  <v-expansion-panel-content>
                    <ts-context-card-approach :approachJSON="approach"></ts-context-card-approach>
                  </v-expansion-panel-content>
                  <v-divider v-if="index != activeContext.question.approaches.length - 1"></v-divider>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>
          </v-expand-transition>
        </div>
        <v-divider></v-divider>

        <!-- Conclusions -->
        <div class="mb-3 pl-5 mt-3">
          <strong style="font-size: 0.9em">Conclusion</strong>
          <v-sheet
            outlined
            rounded
            class="mr-3 pa-3 mt-2"
            style="max-width: 500px"
            v-for="conclusion in activeContext.question.conclusions"
            :key="conclusion.id"
          >
            <ts-question-conclusion
              :question="activeContext.question"
              :conclusion="conclusion"
            ></ts-question-conclusion>
          </v-sheet>
        </div>

        <div v-if="!currentUserConclusion" style="font-size: 0.9em; max-width: 500px" class="pb-4 pl-5 mt-n1">
          <v-textarea
            v-model="conclusionText"
            class="mt-3"
            outlined
            flat
            hide-details
            auto-grow
            rows="2"
            placeholder="Add your conclusion..."
            style="font-size: 0.9em; background-color: white"
          >
          </v-textarea>
          <v-card-actions v-if="conclusionText" class="pb-0">
            <v-spacer></v-spacer>
            <v-btn small text color="primary" @click="createConclusion()" :disabled="!conclusionText"> Save </v-btn>
          </v-card-actions>
        </div>
      </div>
    </v-expand-transition>
  </v-card>
</template>

<script>
import ApiClient from '../../utils/RestApiClient.js'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import TsContextCardApproach from './ContextCardApproach.vue'
import TsSearchChip from './SearchChip.vue'
import TsQuestionConclusion from './QuestionConclusion.vue'

export default {
  components: { TsContextCardApproach, TsSearchChip, TsQuestionConclusion },
  data: function () {
    return {
      showApproaches: false,
      expanded: true,
      conclusionText: '',
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    currentUser() {
      return this.$store.state.currentUser
    },
    activeContext() {
      return this.$store.state.activeContext
    },
    currentUserConclusion() {
      return this.activeContext.question.conclusions.filter(
        (conclusion) => conclusion.user.username === this.currentUser
      ).length
    },
    opensearchQueries() {
      let opensearchQueries = []
      let approaches = this.activeContext.question.approaches.map((approach) => JSON.parse(approach.spec_json))
      approaches.forEach((approach) => {
        approach._view.processors.forEach((processor) => {
          processor.analysis.forEach((analysis) => {
            if (analysis.name === 'OpenSearch') {
              analysis.steps.forEach((step) => {
                if (step.type === 'opensearch-query') {
                  opensearchQueries.push(step)
                }
              })
            }
          })
        })
      })
      return opensearchQueries
    },
  },
  methods: {
    toHtml(markdown) {
      return DOMPurify.sanitize(marked(markdown))
    },
    getDfiqQuestionUrl(id) {
      return 'https://dfiq.org/questions/' + id + '/'
    },
    setActiveQuestion(question) {
      let payload = {
        scenario: this.activeContext.scenario,
        facet: this.activeContext.facet,
        question: question,
      }
      this.$store.dispatch('setActiveContext', payload)
    },
    createConclusion() {
      ApiClient.createQuestionConclusion(this.sketch.id, this.activeContext.question.id, this.conclusionText)
        .then((response) => {
          let newQuestion = response.data.objects[0]
          this.conclusionText = ''
          this.$store.dispatch('updateScenarios', this.sketch.id)
          this.setActiveQuestion(newQuestion)
        })
        .catch((e) => {})
    },
  },
}
</script>

