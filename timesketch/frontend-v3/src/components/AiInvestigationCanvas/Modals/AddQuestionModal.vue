<!--
Copyright 2025 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
  <v-container fluid class="modal pa-5 rounded-lg">
    <div class="modal__loader" v-if="isSubmitting">
      <v-progress-circular
        :size="80"
        :width="4"
        color="primary"
        indeterminate
      ></v-progress-circular>
    </div>
    <div :class="{ modal__content: true, 'no-pointer-events': isSubmitting }">
      <div>
        <h3 class="mb-4">Create Question</h3>
        <div class="d-flex align-center mb-4">
          <v-text-field
            v-model="queryString"
            placeholder="Find a question, or create a new one..."
            autofocus
            hide-details
            solo
            :disabled="isLoading"
            variant="outlined"
            @keyup.enter="createQuestion()"
          >
            <v-icon left icon="mdi-magnify" small />
            <v-btn
              depressed
              small
              class="create-question text-none text-uppercase ml-4"
              :disabled="!queryString || isLoading"
              color="primary"
              @click="createQuestion()"
            >
              <v-icon left icon="mdi-plus" small />
              Create Question
            </v-btn>
          </v-text-field>
        </div>
      </div>
      <div class="questions-group">
        <AddQuestionModalLoader v-if="isLoading" />
        <div v-else>
          <v-list v-if="dfiqMatches && dfiqMatches.length > 0">
            <v-list-subheader class="font-weight-bold">
              DFIQ Suggestions
              <span>({{ dfiqMatches.length }})</span></v-list-subheader
            >
            <div>
              <v-list-item
                v-for="(question, index) in dfiqMatches"
                :key="index"
                @click="createQuestion(question, question.id)"
                class="d-flex"
              >
                <template v-slot:prepend>
                  <v-icon small class="mr-2">mdi-plus</v-icon>
                </template>
                <v-list-item-title> {{ question.name }}</v-list-item-title>
              </v-list-item>
            </div>
          </v-list>
        </div>
      </div>
      <div class="dfiq-notice pt-4">
        <p>
          Explore the complete list of <strong>DFIQ</strong> (Digital Forensics
          Investigative Questions), designed to guide investigations and ensure
          thorough analysis.
        </p>

        <v-btn
          small
          color="primary"
          href="https://dfiq.org/questions"
          target="_external"
        >
          <v-icon left icon="mdi-open-in-new" small />
          Visit DFIQ
        </v-btn>
      </div>
    </div>
  </v-container>
</template>

<script>
import { useAppStore } from "@/stores/app"
import RestApiClient from "@/utils/RestApiClient"
import AddQuestionModalLoader from "../Loaders/AddQuestionModalLoader.vue"

export default {
  inject: ["addNewQuestion"],
  props: {
    questions: Array,
    questionsTotal: Number,
    completedQuestionsTotal: Number,
  },
  data() {
    return {
      isLoading: true,
      queryString: null,
      dfiqTemplates: [],
      isSubmitting: false,
      store: useAppStore(),
    }
  },
  created() {
    this.fetchQuestionTemplates()
  },
  computed: {
    sortedQuestions() {
      return this.questions && this.questions.length > 0
        ? [
            ...this.questions.sort(
              (questionA, questionB) =>
                new Date(questionA.updated_at) - new Date(questionB.updated_at)
            ),
          ]
        : []
    },
    dfiqMatches() {
      if (!this.queryString) {
        return this.dfiqTemplates
      }

      return this.dfiqTemplates.filter((template) =>
        template.name.toLowerCase().includes(this.queryString.toLowerCase())
      )
    },
  },
  methods: {
    async fetchQuestionTemplates() {
      try {
        const dfiqTemplatesRes = await RestApiClient.getQuestionTemplates()

        if (
          dfiqTemplatesRes.data?.objects &&
          dfiqTemplatesRes.data.objects.length > 0
        ) {
          this.dfiqTemplates = dfiqTemplatesRes.data.objects
        }
      } catch (error) {
        console.error(error)
      } finally {
        this.isLoading = false
      }
    },
    async createQuestion(question, templateId) {
      this.isSubmitting = true

      let questionText = question || this.queryString

      if (templateId) {
        questionText = question?.name
        templateId = templateId
      }

      try {
        const questionResponse = await RestApiClient.createQuestion(
          this.store.sketch.id,
          null,
          null,
          questionText,
          templateId
        )

        const questionData = questionResponse.data.objects[0]

        this.addNewQuestion(questionData)
        this.store.setActiveQuestion(questionData)
        this.$emit("close-modal")

        this.store.setNotification({
          text: `You added the question "${questionData.name}" to this Sketch`,
          icon: "mdi-plus-circle-outline",
          type: "success",
        })
      } catch (error) {
        console.error(error)
        this.store.setNotification({
          text: "Unable to add question to this Sketch. Please try again.",
          icon: "mdi-alert-circle-outline",
          type: "error",
        })
      } finally {
        this.isSubmitting = false
      }
    },
  },
}
</script>

<style scoped>
.modal {
  width: 700px;
  height: 538px;
  background-color: #fff;
}

.modal__content {
  display: grid;
  grid-template-rows: auto 300px auto;
}

.modal__loader {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 3;
  background: rgba(255, 255, 255, 0.7);
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.create-question {
  z-index: 3;
  order: 2;
}

.questions-group {
  -ms-overflow-style: none;
  scrollbar-width: none;
  overflow-y: auto;
}

.dfiq-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  border-top: 1px dashed #dadce0;
  font-size: 14px;
}

.no-pointer-events {
  pointer-events: none;
}
</style>
