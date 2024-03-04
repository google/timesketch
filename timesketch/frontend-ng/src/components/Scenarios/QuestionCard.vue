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
  <div>
    <!-- New question -->
    <v-card
      v-if="showQuestionForm || !Object.keys(question).length"
      class="mx-3 mb-3 mt-1"
      flat
      :class="$vuetify.theme.dark ? 'context-card-dark-blue-background' : 'context-card-light-blue-background'"
    >
      <v-toolbar flat dense style="background-color: transparent">
        <v-icon color="primary">mdi-chevron-right</v-icon>
        <v-text-field
          v-model="newTitle"
          label="Create a new investigative question"
          placeholder="Create a new investigative question"
          hide-details
          single-line
          dense
          flat
          solo
          autofocus
          background-color="transparent"
          class="mt-n1 ml-n1"
          :class="$vuetify.theme.dark ? 'custom-placeholder-dark-theme' : 'custom-placeholder-light-theme'"
          @blur="createQuestion"
          @keydown.enter="createQuestion"
          @keydown.esc="newTitle = ''"
          style="font-weight: bold; color: green !important"
        >
        </v-text-field>
        <v-spacer></v-spacer>
        <v-btn color="primary" small text v-if="Object.keys(question).length" @click="showQuestionForm = false"
          >Cancel</v-btn
        >
      </v-toolbar>
    </v-card>

    <!-- Selected question -->
    <v-card
      v-else
      class="mx-3 mb-3 mt-1"
      outlined
      :class="$vuetify.theme.dark ? '' : 'context-card-light-grey-background'"
    >
      <v-toolbar flat dense style="background-color: transparent">
        <span @click="expanded = !expanded" class="ml-n2">
          <v-icon v-if="expanded">mdi-chevron-down</v-icon>
          <v-icon v-else>mdi-chevron-right</v-icon>
          <strong>
            <span style="cursor: pointer">
              {{ question.display_name }}
            </span>
          </strong>
        </span>
        <v-spacer></v-spacer>
        <v-btn
          v-if="question.dfiq_identifier"
          depressed
          small
          :href="getDfiqQuestionUrl(question.dfiq_identifier)"
          target="_blank"
          rel="noreferrer"
          ><v-icon small class="mr-1">mdi-open-in-new</v-icon>{{ question.dfiq_identifier }}
        </v-btn>
        <v-btn small text color="primary" @click="showQuestionForm = true"
          ><v-icon small class="mr-1">mdi-plus</v-icon> New Question</v-btn
        >
      </v-toolbar>
      <v-expand-transition>
        <div v-show="expanded">
          <v-tabs v-model="activeTab" background-color="transparent">
            <v-tab :disabled="!question.approaches.length" class="text-none">
              <v-badge
                v-if="question.approaches.length"
                inline
                :color="$vuetify.theme.dark ? 'secondary' : '#888'"
                :content="question.approaches.length"
              >
                Approaches
              </v-badge>
              <span v-else>Approaches</span>
            </v-tab>

            <v-tab :disabled="!question.description" class="text-none">Description</v-tab>

            <v-tab :disabled="!allSuggestedQueries.length" class="text-none">
              <v-badge
                v-if="allSuggestedQueries.length"
                inline
                :color="$vuetify.theme.dark ? 'secondary' : '#888'"
                :content="allSuggestedQueries.length"
              >
                Suggested Queries
              </v-badge>
              <span v-else>Suggested Queries</span>
            </v-tab>
            <v-tab class="text-none">
              <v-badge
                v-if="question.conclusions.length"
                inline
                :color="$vuetify.theme.dark ? 'secondary' : '#888'"
                :content="question.conclusions.length"
              >
                Conclusions
              </v-badge>
              <span v-else>Conclusions</span>
            </v-tab>
          </v-tabs>
          <v-tabs-items v-model="activeTab" style="background-color: transparent">
            <!--Approaches-->
            <v-tab-item :transition="false">
              <div v-if="question.approaches && question.approaches.length">
                <v-divider></v-divider>
                <v-expansion-panels flat accordion hover mandatory>
                  <v-expansion-panel
                    v-for="(approach, index) in question.approaches"
                    :key="approach.display_name"
                    style="background-color: transparent"
                  >
                    <v-expansion-panel-header expand-icon="">
                      <template v-slot:default="{ open }">
                        <div class="ml-2">
                          <v-icon class="mr-2 ml-n4">
                            <template v-if="open">mdi-chevron-down</template>
                            <template v-else>mdi-chevron-right</template>
                          </v-icon>
                          <strong>{{ approach.display_name }}</strong>
                        </div>
                      </template>
                    </v-expansion-panel-header>
                    <v-expansion-panel-content>
                      <ts-question-approach :approachJSON="approach"></ts-question-approach>
                    </v-expansion-panel-content>
                    <v-divider v-if="index != question.approaches.length - 1"></v-divider>
                  </v-expansion-panel>
                </v-expansion-panels>
              </div>
            </v-tab-item>
            <!-- Description -->
            <v-tab-item :transition="false">
              <div v-if="question.description">
                <v-divider></v-divider>
                <div
                  class="pa-4 markdown-body"
                  style="background-color: transparent; font-size: 0.9em"
                  v-html="toHtml(question.description)"
                ></div>
              </div>
            </v-tab-item>
            <!-- Suggested queries -->
            <v-tab-item :transition="false">
              <div v-if="allSuggestedQueries.length">
                <v-divider></v-divider>
                <div class="pa-4 markdown-body" style="background-color: transparent">
                  <ts-search-chip
                    v-for="query in allSuggestedQueries"
                    :key="query.value"
                    :searchchip="query"
                    type="chip"
                    class="mb-1"
                  ></ts-search-chip>
                </div>
              </div>
            </v-tab-item>
            <!-- Conclusions -->
            <v-tab-item :transition="false">
              <v-divider></v-divider>
              <div class="pa-4 markdown-body" style="background-color: transparent">
                <!-- Existing conclusions -->
                <div>
                  <v-sheet
                    outlined
                    rounded
                    class="pa-3"
                    style="max-width: 500px"
                    v-for="conclusion in question.conclusions"
                    :key="conclusion.id"
                  >
                    <ts-question-conclusion
                      :question="question"
                      :conclusion="conclusion"
                      @delete="deleteConclusion(conclusion)"
                      @new-conclusion="$emit('new-conclusion')"
                    ></ts-question-conclusion>
                  </v-sheet>
                </div>

                <!-- New conclusion -->
                <div v-if="!currentUserConclusion" style="font-size: 0.9em; max-width: 500px">
                  <v-textarea
                    v-model="conclusionText"
                    outlined
                    flat
                    hide-details
                    auto-grow
                    rows="2"
                    placeholder="Add your conclusion..."
                    style="font-size: 0.9em"
                    :class="$vuetify.theme.dark ? '' : 'textfield-light-background'"
                  >
                  </v-textarea>
                  <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn small text @click="conclusionText = ''" :disabled="!conclusionText"> Cancel </v-btn>
                    <v-btn small text color="primary" @click="createConclusion()" :disabled="!conclusionText">
                      Save
                    </v-btn>
                  </v-card-actions>
                </div>
              </div>
            </v-tab-item>
          </v-tabs-items>
        </div>
      </v-expand-transition>
    </v-card>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient.js'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import TsSearchChip from './SearchChip.vue'
import TsQuestionApproach from './QuestionApproach.vue'
import TsQuestionConclusion from './QuestionConclusion.vue'

export default {
  props: {
    scenario: Object,
    facet: Object,
    question: Object,
  },
  components: {
    TsQuestionApproach,
    TsQuestionConclusion,
    TsSearchChip,
  },
  data: function () {
    return {
      expanded: false,
      conclusionText: '',
      activeTab: 0,
      newTitle: '',
      currentTitle: '',
      showQuestionForm: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    currentUser() {
      return this.$store.state.currentUser
    },
    currentUserConclusion() {
      if (!this.question.conclusions) {
        return false
      }
      return this.question.conclusions.filter((conclusion) => conclusion.user.username === this.currentUser).length
    },
    allSuggestedQueries() {
      let queries = []
      let approaches = this.question.approaches.map((approach) => JSON.parse(approach.spec_json))
      approaches.forEach((approach) => {
        approach._view.processors.forEach((processor) => {
          processor.analysis.forEach((analysis) => {
            if (analysis.name === 'OpenSearch') {
              analysis.steps.forEach((step) => {
                queries.push(step)
              })
            }
          })
        })
      })
      return queries
    },
  },
  methods: {
    createQuestion() {
      if (this.newTitle.trim() === '') {
        this.newTitle = ''
        return
      }
      this.currentTitle = this.newTitle
      ApiClient.createQuestion(this.sketch.id, this.scenario.id, this.facet.id, this.newTitle)
        .then((response) => {
          let newQuestion = response.data.objects[0]
          this.newTitle = ''
          this.showQuestionForm = false
          this.$emit('new-question', newQuestion)
        })
        .catch((e) => {
          console.error(e)
        })
    },
    createConclusion() {
      ApiClient.createQuestionConclusion(this.sketch.id, this.question.id, this.conclusionText)
        .then((response) => {
          this.conclusionText = ''
          this.$emit('refresh-question')
        })
        .catch((e) => {
          console.error(e)
        })
    },
    deleteConclusion(conclusion) {
      ApiClient.deleteQuestionConclusion(this.sketch.id, this.question.id, conclusion.id)
        .then((response) => {
          this.$emit('refresh-question')
        })
        .catch((e) => {
          console.error(e)
        })
    },
    toHtml(markdown) {
      return DOMPurify.sanitize(marked(markdown))
    },
    getDfiqQuestionUrl(id) {
      return 'https://dfiq.org/questions/' + id + '/'
    },
  },
  watch: {
    question: function (newQuestion) {
      // Select initial active tab
      if (Object.keys(newQuestion).length) {
        // Always show conclusions if there are any
        if (newQuestion.conclusions.length > 0) {
          this.activeTab = 3
          this.expanded = true
          // Otherwise show approaches if there are any
        } else if (newQuestion.approaches.length > 0) {
          this.activeTab = 0
          this.expanded = true
          // Finally show conclusions
        } else {
          this.activeTab = 3
        }
      }
    },
  },
}
</script>

<style>
.icon {
  order: 0;
}

.header {
  order: 1;
}

.custom-placeholder-light-theme ::placeholder {
  opacity: 0.7;
  color: #1976d2 !important;
}

.custom-placeholder-light-theme label {
  opacity: 1;
  color: #1976d2 !important;
}

.custom-placeholder-light-theme input {
  color: #1976d2 !important;
}

.custom-placeholder-dark-theme ::placeholder {
  opacity: 0.7;
  color: #ffffff !important;
}

.custom-placeholder-dark-theme label {
  opacity: 1;
  color: #ffffff !important;
}

.truncate-with-ellipsis {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.context-card-light-grey-background {
  background-color: #fafafa !important;
}
.context-card-light-blue-background {
  background-color: #e3eef9 !important;
}
.context-card-dark-blue-background {
  background-color: #00436360 !important;
}
.textfield-light-background {
  background-color: #fff !important;
}
</style>
