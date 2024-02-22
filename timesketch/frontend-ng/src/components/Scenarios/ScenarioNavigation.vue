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
  <v-container fluid class="mb-n2 mt-2">
    <!-- Navigation -->
    <div>
      <!-- Loading -->
      <div v-if="isLoading" class="ml-4" style="font-size: 0.9em">
        <v-progress-circular :size="20" :width="1" indeterminate color="primary" class="mr-3"></v-progress-circular>
        Loading scenarios..
      </div>
      <!-- Dropdown menus -->
      <div v-else class="d-flex flex-row ml-4" style="font-size: 0.9em">
        <!-- Scenarios -->
        <v-menu offset-y>
          <template v-slot:activator="{ on, attrs }">
            <div v-bind="attrs" v-on="on" class="d-flex flex-row">
              <span v-if="activeScenario.display_name" class="truncate-with-ellipsis" style="max-width: 250px">
                <strong>{{ activeScenario.display_name }}</strong>
              </span>
              <span v-else> Select a scenario </span>
              <v-icon small class="ml-1">mdi-chevron-down</v-icon>
            </div>
          </template>
          <v-card>
            <v-list v-if="activeScenarios.length" style="max-height: 500px; max-width: 600px" class="overflow-y-auto">
              <v-list-item-group>
                <v-list-item v-if="Object.keys(activeScenario).length" @click="setActiveScenario({})">
                  <v-list-item-content>
                    <v-list-item-title style="opacity: 0.6">Clear selected scenario</v-list-item-title>
                  </v-list-item-content>
                  <v-list-item-action>
                    <v-btn icon>
                      <v-icon color="grey">mdi-close</v-icon>
                    </v-btn>
                  </v-list-item-action>
                </v-list-item>
                <ts-scenario-list-item
                  v-for="(scenario, index) in activeScenarios"
                  :key="index"
                  :scenario="scenario"
                  @set-active-scenario="setActiveScenario(scenario)"
                  @set-scenario-status="setScenarioStatus(scenario.id, $event)"
                  @rename-scenario="renameScenario($event)"
                  @copy-scenario="copyScenario($event)"
                  title="Switch to this scenario"
                >
                </ts-scenario-list-item>
              </v-list-item-group>
            </v-list>

            <div v-if="deletedScenarios.length" class="pt-2">
              <span
                style="cursor: pointer; font-size: small"
                class="ml-3"
                @click.stop="showDeletedScenarios = !showDeletedScenarios"
              >
                <v-icon v-if="!showDeletedScenarios" small>mdi-chevron-right</v-icon>
                <v-icon v-else small>mdi-chevron-down</v-icon>
                {{ deletedScenarios.length }} scenarios in trash
              </span>
              <v-expand-transition>
                <v-list>
                  <v-list-item-group v-if="showDeletedScenarios">
                    <v-list-item
                      title="Restore scenario"
                      v-for="(scenario, index) in deletedScenarios"
                      :key="index"
                      @click.stop="setScenarioStatus(scenario.id, 'active')"
                    >
                      <v-list-item-content style="max-width: 300px">
                        <v-list-item-title style="opacity: 0.8">{{ scenario.display_name }}</v-list-item-title>
                      </v-list-item-content>
                      <v-list-item-action>
                        <v-btn icon>
                          <v-icon color="grey">mdi-arrow-u-left-top</v-icon>
                        </v-btn>
                      </v-list-item-action>
                    </v-list-item>
                  </v-list-item-group>
                </v-list>
              </v-expand-transition>
            </div>

            <v-divider></v-divider>
            <v-list style="max-height: 500px; max-width: 600px" class="overflow-y-auto">
              <v-subheader>Create scenario from template</v-subheader>
              <v-list-item-group>
                <v-list-item
                  v-for="(scenario, index) in scenarioTemplates"
                  :key="index"
                  @click="createScenarioFromTemplate(scenario.id)"
                  title="Create scenario from this template"
                >
                  <v-list-item-content style="max-width: 300px">
                    <v-list-item-title> {{ scenario.name }}</v-list-item-title>

                    <v-list-item-subtitle :title="scenario.description">{{
                      scenario.description
                    }}</v-list-item-subtitle>
                  </v-list-item-content>
                  <v-list-item-action>
                    <v-btn icon>
                      <v-icon color="grey lighten-1">mdi-plus</v-icon>
                    </v-btn>
                  </v-list-item-action>
                </v-list-item>
              </v-list-item-group>
            </v-list>
          </v-card>
        </v-menu>
        <!-- Facets -->
        <v-menu :disabled="!facetList.length" offset-y v-model="showFacetMenu">
          <template v-slot:activator="{ on, attrs }">
            <div v-bind="attrs" v-on="on" class="d-flex flex-row ml-5">
              <span
                v-if="activeFacet.display_name"
                :title="activeFacet.display_name"
                class="truncate-with-ellipsis"
                style="max-width: 250px"
              >
                <strong>{{ activeFacet.display_name }}</strong>
              </span>
              <span v-else :class="facetList.length ? '' : 'disabled'">Select an investigation</span>
              <v-icon small class="ml-1">mdi-chevron-down</v-icon>
            </div>
          </template>

          <v-list v-if="facetList.length" style="max-width: 600px">
            <v-list-item-group>
              <v-list-item v-for="(facet, index) in facetList" :key="index" @click="setActiveFacet(facet)">
                <v-list-item-content>
                  <v-list-item-title>{{ facet.display_name }}</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </v-list-item-group>
          </v-list>
        </v-menu>
        <!-- Questions -->
        <v-menu :disabled="!questionList.length" offset-y v-model="showQuestionMenu">
          <template v-slot:activator="{ on, attrs }">
            <div v-bind="attrs" v-on="on" class="d-flex flex-row ml-5">
              <span
                v-if="activeQuestion.display_name"
                :title="activeQuestion.display_name"
                class="truncate-with-ellipsis"
                style="max-width: 350px"
              >
                <strong>{{ activeQuestion.display_name }}</strong>
              </span>
              <span v-else :class="questionList.length ? '' : 'disabled'"> Select a question to answer </span>
              <v-icon small class="ml-1">mdi-chevron-down</v-icon>
            </div>
          </template>
          <v-card>
            <v-list style="max-height: 500px; max-width: 600px" class="overflow-y-auto">
              <v-list-item-group>
                <v-list-item v-if="Object.keys(activeQuestion).length" @click="setActiveQuestion({})">
                  <v-list-item-content>
                    <v-list-item-title style="opacity: 0.6">Clear selected question</v-list-item-title>
                  </v-list-item-content>
                  <v-list-item-action>
                    <v-btn icon>
                      <v-icon color="grey">mdi-close</v-icon>
                    </v-btn>
                  </v-list-item-action>
                </v-list-item>

                <v-list-item
                  v-for="(question, index) in questionList"
                  :key="index"
                  @click="setActiveQuestion(question)"
                >
                  <v-list-item-title>{{ question.display_name }}</v-list-item-title>
                </v-list-item>
              </v-list-item-group>
            </v-list>
          </v-card>
        </v-menu>
      </div>
    </div>
    <!-- Question card -->
    <div class="mt-5">
      <ts-question-card
        :scenario="activeScenario"
        :facet="activeFacet"
        :question="activeQuestion"
        @new-question="setActiveQuestion"
        @new-conclusion="refreshActiveQuestion"
        @refresh-question="refreshActiveQuestion"
      ></ts-question-card>
    </div>
  </v-container>
</template>

<script>
import ApiClient from '../../utils/RestApiClient.js'
import TsQuestionCard from './QuestionCard.vue'
import TsScenarioListItem from './ScenarioListItem.vue'

export default {
  components: {
    TsQuestionCard,
    TsScenarioListItem,
  },
  data: function () {
    return {
      isLoading: false,
      showDeletedScenarios: false,
      scenarioList: [],
      facetList: [],
      questionList: [],
      showScenarioMenu: false,
      showFacetMenu: false,
      showQuestionMenu: false,
      activeScenario: {},
      activeFacet: {},
      activeQuestion: {},
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    scenarioTemplates() {
      return this.$store.state.scenarioTemplates
    },
    activeScenarios() {
      if (!this.scenarioList) return []
      return this.scenarioList.filter((scenario) => !scenario.status.length || scenario.status[0].status === 'active')
    },
    deletedScenarios() {
      if (!this.scenarioList) return []
      return this.scenarioList.filter((scenario) => scenario.status.length && scenario.status[0].status === 'deleted')
    },
  },
  methods: {
    fetchScenarioList(showLoading = false) {
      if (showLoading) {
        this.isLoading = true
      }
      return ApiClient.getSketchScenarios(this.sketch.id)
        .then((response) => {
          this.scenarioList = response.data.objects[0]
          this.isLoading = false
        })
        .catch((e) => {
          console.error(e)
          this.isLoading = false
        })
    },
    createScenarioFromTemplate(templateId, displayName = null, setActive = true) {
      ApiClient.addScenario(this.sketch.id, templateId, displayName)
        .then((response) => {
          const scenario = response.data.objects[0]
          this.scenarioList.push(scenario)
          this.fetchScenarioList()
          if (setActive) {
            this.setActiveScenario(scenario)
          }
        })
        .catch((e) => {
          console.error(e)
        })
    },
    copyScenario(scenarioToCopy) {
      const displayName = 'Copy of ' + scenarioToCopy.display_name
      const templateId = scenarioToCopy.dfiq_identifier
      this.createScenarioFromTemplate(templateId, displayName, false)
    },
    setScenarioStatus(scenarioId, status) {
      ApiClient.setScenarioStatus(this.sketch.id, scenarioId, status)
        .then((response) => {
          if (status === 'deleted') {
            this.scenarioList = this.scenarioList.filter((scenario) => scenario.id !== scenarioId)
          }
          this.fetchScenarioList()
        })
        .catch((e) => {
          console.error(e)
        })
    },
    renameScenario(scenario) {
      this.fetchScenarioList()
      this.setActiveScenario(scenario, false)
    },
    setActiveScenario(scenario, showMenu = true, setActiveContext = true) {
      this.activeScenario = scenario
      this.facetList = []
      this.questionList = []
      this.activeFacet = {}
      this.activeQuestion = {}
      if (!Object.keys(scenario).length) {
        this.refreshQuestionList()
        this.setActiveContext(undefined)
        return
      }
      if (setActiveContext) {
        this.setActiveContext(scenario.id)
      }
      return ApiClient.getFacets(this.sketch.id, scenario.id)
        .then((response) => {
          this.facetList = response.data.objects[0]
          if (showMenu) {
            this.showFacetMenu = true
          }
        })
        .catch((e) => {
          console.error(e)
        })
        .then(() => {
          this.refreshQuestionList()
        })
    },
    setActiveFacet(facet, showMenu = true) {
      this.activeFacet = facet
      this.questionList = []
      this.activeQuestion = {}
      this.setActiveContext(this.activeScenario.id, facet.id)
      return ApiClient.getFacetQuestions(this.sketch.id, this.activeScenario.id, facet.id)
        .then((response) => {
          this.questionList = response.data.objects[0]
          if (showMenu) {
            this.showQuestionMenu = true
          }
        })
        .catch((e) => {
          console.error(e)
        })
    },
    setActiveQuestion(question) {
      this.activeQuestion = question
      this.setActiveContext(this.activeScenario.id, this.activeFacet.id, question.id)
      this.refreshActiveQuestion()
    },
    setActiveContext(scenarioId, facetId, questionId) {
      let payload = {
        scenarioId: scenarioId,
        facetId: facetId,
        questionId: questionId,
      }
      this.$store.dispatch('setActiveContext', payload)
    },
    refreshQuestionList() {
      if (Object.keys(this.activeFacet).length) {
        ApiClient.getFacetQuestions(this.sketch.id, this.activeScenario.id, this.activeFacet.id)
          .then((response) => {
            this.questionList = response.data.objects[0]
          })
          .catch((e) => {
            console.error(e)
          })
      } else if (Object.keys(this.activeScenario).length) {
        ApiClient.getScenarioQuestions(this.sketch.id, this.activeScenario.id)
          .then((response) => {
            this.questionList = response.data.objects[0]
          })
          .catch((e) => {
            console.error(e)
          })
      } else {
        ApiClient.getOrphanQuestions(this.sketch.id)
          .then((response) => {
            let questionList = response.data.objects[0]
            if (!questionList) {
              this.questionList = []
              return
            }
            this.questionList = questionList
          })
          .catch((e) => {
            console.error(e)
          })
      }
    },
    refreshActiveQuestion() {
      ApiClient.getQuestion(this.sketch.id, this.activeQuestion.id)
        .then((response) => {
          this.activeQuestion = response.data.objects[0]
          this.refreshQuestionList()
        })
        .catch((e) => {
          console.error(e)
        })
    },
  },
  mounted() {
    // TODO: Add support for query parameters to select a scenario, facet, and question
    this.fetchScenarioList(true).then(() => {
      // Fetch and set the active question from local storage, if it exists
      let storageKey = 'sketchContext' + this.sketch.id.toString()
      let storedContext = localStorage.getItem(storageKey)
      let context = {}
      if (storedContext) {
        context = JSON.parse(storedContext)
      }
      if (Object.keys(context).length) {
        if (context.questionId && !context.facetId && !context.scenarioId) {
          ApiClient.getQuestion(this.sketch.id, context.questionId)
            .then((response) => {
              let question = response.data.objects[0]
              this.setActiveQuestion(question)
            })
            .catch((e) => {
              console.error(e)
            })
        }

        if (context.scenarioId && !context.facetId) {
          let scenario = this.scenarioList.find((scenario) => scenario.id === context.scenarioId)
          this.setActiveScenario(scenario, false, false)
        }

        if (context.scenarioId && context.facetId) {
          let scenario = this.scenarioList.find((scenario) => scenario.id === context.scenarioId)
          this.setActiveScenario(scenario, false, false).then(() => {
            if (context.facetId) {
              let facet = this.facetList.find((facet) => facet.id === context.facetId)
              this.setActiveFacet(facet, false).then(() => {
                if (context.questionId) {
                  let question = this.questionList.find((question) => question.id === context.questionId)
                  this.setActiveQuestion(question)
                }
              })
            }
          })
        }
        this.setActiveContext(this.activeScenario.id, this.activeFacet.id, this.activeQuestion.id)
      } else {
        this.refreshQuestionList()
      }
    })
  },
}
</script>

<style lang="scss">
.truncate-with-ellipsis {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.disabled {
  opacity: 0.3;
}
</style>
