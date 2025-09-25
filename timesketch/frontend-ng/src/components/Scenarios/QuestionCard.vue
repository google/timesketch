<!--
Copyright 2024 Google Inc. All rights reserved.

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
  <v-container fluid>
    <v-card class="mx-3 mt-3 mb-3" outlined :class="$vuetify.theme.dark ? '' : 'context-card-light-grey-background'">
      <v-toolbar flat dense style="background-color: transparent">
        <span v-if="isLoading">
          <v-progress-circular :size="20" :width="1" indeterminate color="primary" class="mr-3"></v-progress-circular>
        </span>
        <span v-if="activeQuestion.display_name" id="questionDropdownButton" style="cursor: pointer; font-size: 1.1em">
          <span @click="expanded = !expanded">
            <v-icon v-if="expanded">mdi-chevron-down</v-icon>
            <v-icon v-else>mdi-chevron-right</v-icon>
            <strong>
              <span class="ml-2 mr-3">
                <span>{{ activeQuestion.display_name }} </span>
              </span>
            </strong>
          </span>
          <v-btn small depressed class="text-none" color="primary" @click="showDropdown = !showDropdown">
            Change question
            <v-icon small right>mdi-chevron-down</v-icon>
          </v-btn>
        </span>

        <span v-if="showEmptySelect && !isLoading">
          <v-btn depressed class="text-none ml-n2" color="primary" @click="showDropdown = !showDropdown">
            Select or create an investigative question
          </v-btn>
        </span>
      </v-toolbar>

      <v-card
        v-if="showDropdown && !isLoading"
        style="position: absolute; z-index: 1000"
        elevation="10"
        outlined
        width="50%"
        v-click-outside="onClickOutside"
      >
        <v-row>
          <v-col cols="12">
            <v-card outlined class="ma-2">
              <v-text-field
                v-model="queryString"
                placeholder="Find a question, or create a new one.."
                class="mx-2 mb-1"
                autofocus
                hide-details
                dense
                single-line
                flat
                solo
                @keyup.enter="createQuestion()"
              >
                <template v-slot:append>
                  <v-btn
                    depressed
                    small
                    class="text-none mt-1 mr-n3"
                    :disabled="!queryString"
                    color="primary"
                    @click="createQuestion()"
                  >
                    <v-icon left small>mdi-plus</v-icon>
                    Create new question
                  </v-btn>
                </template>
              </v-text-field>
            </v-card>
          </v-col>
        </v-row>
        <v-row no-gutters>
          <v-col cols="12" v-if="matches.questions && matches.questions.length">
            <v-toolbar dense flat>
              <strong
                >Assigned questions for this sketch
                <span style="font-size: 0.7em">({{ matches.questions.length }})</span></strong
              >
            </v-toolbar>

            <v-list style="max-height: 300px" class="overflow-y-auto">
              <v-list-item-group>
                <v-list-item
                  v-for="(question, index) in matches.questions"
                  :key="index"
                  @click="setActiveQuestion(question)"
                >
                  <v-icon
                    small
                    class="mr-2"
                    :disabled="!question.conclusions.length"
                    :color="question.conclusions.length ? 'success' : ''"
                    >mdi-check-circle</v-icon
                  >
                  <v-list-item-title>{{ question.name }}</v-list-item-title>
                </v-list-item>
              </v-list-item-group>
            </v-list>
          </v-col>
        </v-row>

        <v-row no-gutters>
          <v-col cols="12" v-if="matches.templates.length">
            <v-toolbar dense flat>
              <strong
                >Add DFIQ question <span style="font-size: 0.7em">({{ matches.templates.length }})</span></strong
              >
            </v-toolbar>
            <v-list style="height: 300px" class="overflow-y-auto">
              <v-list-item-group>
                <v-list-item
                  v-for="(question, index) in matches.templates"
                  :key="index"
                  @click="createQuestion(question)"
                >
                  <v-icon small class="mr-2">mdi-plus</v-icon>
                  <v-list-item-content>
                    <v-list-item-title> {{ question.name }}</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </v-list-item-group>
            </v-list>
          </v-col>
        </v-row>
      </v-card>

      <v-expand-transition>
        <div v-show="expanded && activeQuestion">
          <v-divider></v-divider>
          <v-row no-gutters>
            <v-col>
              <v-tabs v-model="activeTab" background-color="transparent">
                <v-tab :disabled="allSuggestedQueries.length === 0 && !userSettings.generateQuery" class="text-none">
                  Suggested queries
                  <span class="ml-1"
                    ><small
                      ><strong>({{ allSuggestedQueries.length }})</strong></small
                    ></span
                  >
                </v-tab>

                <v-tab :disabled="!activeQuestion.approaches.length" class="text-none">
                  Approaches
                  <span class="ml-1"
                    ><small
                      ><strong>({{ activeQuestion.approaches.length }})</strong></small
                    ></span
                  >
                </v-tab>

                <v-tab class="text-none">
                  Conclusions
                  <span v-if="activeQuestion.conclusions.length" class="ml-1"
                    ><small
                      ><strong>({{ activeQuestion.conclusions.length }})</strong></small
                    ></span
                  >
                </v-tab>
              </v-tabs>
              <v-tabs-items v-model="activeTab" style="background-color: transparent">
                <!-- Suggested queries -->
                <v-tab-item :transition="false" class="mb-2">
                  <div v-if="allSuggestedQueries.length">
                    <div class="mt-4" style="background-color: transparent">
                      <ts-search-chip
                        v-for="query in allSuggestedQueries"
                        :key="query.value"
                        :searchchip="query"
                        icon="mdi-magnify"
                        type="link"
                      ></ts-search-chip>
                    </div>
                  </div>
                  <div class="mt-1" v-if="isNl2qAvailable">
                    <div v-if="suggestedQueryLoading" class="pa-2 pl-4">
                      <v-skeleton-loader type="sentences" width="200"></v-skeleton-loader>
                    </div>
                    <div v-if="Object.keys(suggestedQuery).length && !suggestedQueryLoading">
                      <ts-search-chip
                        :searchchip="suggestedQuery"
                        type="link"
                        icon="mdi-shimmer"
                        class="mb-1"
                      ></ts-search-chip>
                    </div>
                    <div v-if="!Object.keys(suggestedQuery).length && !suggestedQueryLoading" class="pl-4">
                      <v-btn small depressed light class="text-none mt-2 mb-4 btn-gradient" @click="getSuggestedQuery">
                        <v-icon small left>mdi-shimmer</v-icon>
                        Generate query</v-btn
                      >
                    </div>
                  </div>
                </v-tab-item>
                <!--Approaches-->
                <v-tab-item :transition="false">
                  <div v-if="activeQuestion.approaches && activeQuestion.approaches.length">
                    <div
                      class="pa-4 markdown-body"
                      style="background-color: transparent; font-size: 0.9em"
                      v-html="toHtml(activeQuestion.description)"
                    ></div>

                    <v-expansion-panels flat accordion hover>
                      <v-expansion-panel
                        v-for="(approach, index) in activeQuestion.approaches"
                        :key="index"
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
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </div>
                </v-tab-item>
                <!-- Conclusions -->
                <v-tab-item :transition="false">
                  <div class="pa-4 markdown-body" style="background-color: transparent">
                    <!-- Existing conclusions -->
                    <v-sheet
                      outlined
                      rounded
                      class="pa-3"
                      style="max-width: 500px"
                      v-for="conclusion in activeQuestion.conclusions"
                      :key="conclusion.id"
                    >
                      <ts-question-conclusion
                        :question="activeQuestion"
                        :conclusion="conclusion"
                        @delete="deleteConclusion(conclusion)"
                        @save-conclusion="refreshActiveQuestion()"
                      ></ts-question-conclusion>
                    </v-sheet>
                    <!-- New conclusion -->
                    <div v-if="!currentUserConclusion" style="font-size: 0.9em; max-width: 500px">
                      <v-textarea
                        v-model="conclusionText"
                        outlined
                        flat
                        hide-details
                        auto-grow
                        rows="3"
                        clearable
                        placeholder="Add your conclusion..."
                        style="font-size: 0.9em"
                        :class="$vuetify.theme.dark ? '' : 'textfield-light-background'"
                      >
                      </v-textarea>

                      <v-btn
                        small
                        text
                        class="mt-2"
                        color="primary"
                        @click="createConclusion()"
                        :disabled="!conclusionText"
                      >
                        Save
                      </v-btn>
                    </div>
                  </div>
                </v-tab-item>
              </v-tabs-items>
            </v-col>
          </v-row>
        </div>
      </v-expand-transition>
    </v-card>
  </v-container>
</template>

<script>
import ApiClient from '../../utils/RestApiClient.js'
import EventBus from '../../event-bus.js'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import TsSearchChip from './SearchChip.vue'
import TsQuestionApproach from './QuestionApproach.vue'
import TsQuestionConclusion from './QuestionConclusion.vue'

export default {
  components: {
    TsQuestionApproach,
    TsQuestionConclusion,
    TsSearchChip,
  },
  props: {
    questionId: {
      type: [String, Number],
      default: null,
    },
    initialTab: {
      type: Number,
      default: 0,
      validator: (value) => value >= 0 && value <= 2,
    },
  },
  data: function () {
    return {
      isLoading: false,
      expanded: false,
      questionTemplates: [],
      sketchQuestions: [],
      activeQuestion: {
        approaches: [],
        conclusions: [],
      },
      searchHistory: [],
      conclusionText: '',
      activeTab: 0,
      currentTitle: '',
      queryString: '',
      showDropdown: false,
      showEmptySelect: false,
      suggestedQuery: {},
      suggestedQueryLoading: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    currentUser() {
      return this.$store.state.currentUser
    },
    systemSettings() {
      return this.$store.state.systemSettings
    },
    userSettings() {
      return this.$store.state.settings
    },
    isNl2qAvailable() {
      return (
        this.userSettings.generateQuery &&
        this.systemSettings.LLM_FEATURES_AVAILABLE &&
        this.systemSettings.LLM_FEATURES_AVAILABLE.nl2q
      )
    },
    matches() {
      if (!this.queryString) {
        return {
          questions: this.sketchQuestions,
          templates: this.questionTemplates,
        }
      }
      let matches = {}
      if (this.sketchQuestions) {
        matches['questions'] = this.sketchQuestions.filter((question) =>
          question.name.toLowerCase().includes(this.queryString.toLowerCase())
        )
      }
      if (this.questionTemplates) {
        matches['templates'] = this.questionTemplates.filter((template) =>
          template.name.toLowerCase().includes(this.queryString.toLowerCase())
        )
      }
      return matches
    },
    allSuggestedQueries() {
      if (!this.activeQuestion.approaches.length) {
        return []
      }
      let queries = []
      let approaches = this.activeQuestion.approaches.map((approach) => JSON.parse(approach.spec_json))
      if (approaches) {
        approaches.forEach((approach) => {
          if (approach.steps) {
            approach.steps.forEach((step) => {
              if (step.type === 'opensearch-query') {
                queries.push(step)
              }
            })
          }
        })
      }
      return queries
    },
    currentUserConclusion() {
      if (!this.activeQuestion.conclusions) {
        return false
      }
      return this.activeQuestion.conclusions.filter((conclusion) => conclusion.user.username === this.currentUser)
        .length
    },
  },
  methods: {
    getSuggestedQuery() {
      this.suggestedQueryLoading = true
      let formData = { question: this.activeQuestion.display_name }
      ApiClient.llmRequest(this.sketch.id, 'nl2q', formData)
        .then((response) => {
          this.suggestedQuery = response.data
          this.suggestedQueryLoading = false
        })
        .catch((e) => {
          console.error(e)
        })
    },
    getQuestionTemplates() {
      this.isLoading = true
      ApiClient.getQuestionTemplates()
        .then((response) => {
          this.questionTemplates = response.data.objects
          this.isLoading = false
        })
        .catch((e) => {
          console.error(e)
        })
    },
    getSketchQuestions() {
      this.isLoading = true
      return ApiClient.getOrphanQuestions(this.sketch.id)
        .then((response) => {
          this.sketchQuestions = response.data.objects[0]
          this.isLoading = false
        })
        .catch((e) => {
          console.error(e)
        })
    },
    createQuestion(template = null) {
      let questionText = this.queryString
      let templateId = null

      if (template !== null) {
        questionText = template.name
        templateId = template.id
      }

      ApiClient.createQuestion(this.sketch.id, null, null, questionText, templateId)
        .then((response) => {
          const newQuestion = response.data.objects[0]
          this.setActiveQuestion(newQuestion)
          this.$emit('new-question', newQuestion)
          this.getSketchQuestions()
        })
        .catch((e) => {
          console.error(e)
        })
    },
    getSearchHistory() {
      ApiClient.getSearchHistory(this.sketch.id, 5, this.activeQuestion.id)
        .then((response) => {
          if (response.data.objects.length) {
            this.searchHistory = response.data.objects.reverse()
          } else this.searchHistory = []
        })
        .catch((e) => {
          console.error(e)
        })
    },
    refreshActiveQuestion() {
      ApiClient.getQuestion(this.sketch.id, this.activeQuestion.id)
        .then((response) => {
          this.activeQuestion = response.data.objects[0]
        })
        .catch((e) => {
          console.error(e)
        })
    },
    createConclusion() {
      ApiClient.createQuestionConclusion(this.sketch.id, this.activeQuestion.id, this.conclusionText)
        .then((response) => {
          this.conclusionText = ''
          this.refreshActiveQuestion()
          this.getSketchQuestions()
        })
        .catch((e) => {
          console.error(e)
        })
    },
    deleteConclusion(conclusion) {
      ApiClient.deleteQuestionConclusion(this.sketch.id, this.activeQuestion.id, conclusion.id)
        .then((response) => {
          this.refreshActiveQuestion()
          this.getSketchQuestions()
        })
        .catch((e) => {
          console.error(e)
        })
    },
    setActiveQuestion(question) {
      this.activeQuestion = question
      this.showDropdown = false
      this.showEmptySelect = false
      this.queryString = ''
      this.currentTitle = question.name
      this.expanded = true
      this.suggestedQuery = {}

      // Set active tab
     if (this.isNl2qAvailable) {
       if (this.activeQuestion.conclusions.length) {
         this.activeTab = 2
       } else {
         this.activeTab = 0
       }
     } else {
       if (this.activeQuestion.conclusions.length) {
         this.activeTab = 2
       } else if (this.allSuggestedQueries.length) {
         this.activeTab = 0
       } else if (this.activeQuestion.approaches.length) {
         this.activeTab = 1
       } else {
         this.activeTab = 2
       }
     }


      let payload = {
        scenarioId: null,
        facetId: null,
        questionId: question.id,
      }
      this.$store.dispatch('setActiveContext', payload)
    },
    toHtml(markdown) {
      if (!markdown) {
        return
      }
      return DOMPurify.sanitize(marked(markdown))
    },
    onClickOutside(e) {
      if (e.target.id !== 'questionDropdownButton') {
        this.showDropdown = false
      }
    },
    search(searchHistoryItem) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = searchHistoryItem.query_string
      eventData.queryFilter = JSON.parse(searchHistoryItem.query_filter)
      eventData.incognito = true
      EventBus.$emit('setQueryAndFilter', eventData)
    },
    fetchQuestion(questionId) {
      this.isLoading = true;
      return new Promise((resolve, reject) => {
        ApiClient.getQuestion(this.sketch.id, questionId)
          .then((response) => {
            let data = response.data.objects[0]
            resolve(data)
          })
          .catch((e) => {
            console.error("Error fetching question:", e)
            this.isLoading = false
            this.activeQuestion = null
            this.$emit('error', 'Failed to load question.')
            reject(e)
          })
          .finally(() => {
            this.isLoading = false
          });
      });
    },
  },
  beforeDestroy() {
    EventBus.$off('createBranch')
  },
  mounted() {
    EventBus.$on('createBranch', this.getSearchHistory)
    if (this.questionId) {
      this.fetchQuestion(this.questionId)
        .then((question) => {
          if (question) {
            this.activeQuestion = question
            this.expanded = true
            if (this.initialTab) {
              this.activeTab = this.initialTab
            } else {
              this.activeTab = 2
            }
          } else {
            console.error("No question found with ID: ", this.questionId)
          }
        })
        .catch((error) => {
          console.error("Error in mounted:", error)
        })
    } else {
      let questionUUID = this.$route.query.question_uuid
      this.getQuestionTemplates()
      this.getSketchQuestions().then(() => {
        if (questionUUID) {
          const question = this.sketchQuestions.find((question) => question.uuid === questionUUID)
          if (!question) {
            this.errorSnackBar('No question found with that UUID')
            this.showEmptySelect = true
            return
          }
          this.setActiveQuestion(question)
        }
      })
      if (!questionUUID) {
        // Restore active question from local storage
        let storageKey = 'sketchContext' + this.sketch.id.toString()
        let storedContext = localStorage.getItem(storageKey)
        let context = {}
        if (storedContext) {
          context = JSON.parse(storedContext)
        }
        if (Object.keys(context).length) {
          this.isLoading = true
          ApiClient.getQuestion(this.sketch.id, context.questionId)
            .then((response) => {
              this.setActiveQuestion(response.data.objects[0])
              this.isLoading = false
            })
            .catch((e) => {
              console.error(e)
            })
        } else {
          this.showEmptySelect = true
        }
      }
    }
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
.btn-gradient {
  background: radial-gradient(
    circle at 100% 0%,
    #a0d9f2,
    #a7d9f5,
    #add9f7,
    #b3dafa,
    #b9dafb,
    #bfdafd,
    #c5dbfe,
    #cadbff
  );
}
.skeleton-gradient {
  color: radial-gradient(circle at 100% 0%, #a0d9f2, #a7d9f5, #add9f7, #b3dafa, #b9dafb, #bfdafd, #c5dbfe, #cadbff);
}
</style>
