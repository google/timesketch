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
    <v-progress-linear v-if="loading" color="primary" indeterminate height="2"></v-progress-linear>
    <div @mouseover="showControls = true" @mouseleave="showControls = false" style="position: relative">
      <div style="font-size: 0.9em" class="mb-2">
        <strong>{{ conclusion.user.username }}</strong>
        <small class="ml-3"
          >{{ conclusion.created_at | shortDateTime }} ({{ conclusion.created_at | timeSince }})</small
        >
      </div>

      <div v-if="editable">
        <v-textarea
          style="font-size: 0.9em"
          hide-details
          auto-grow
          outlined
          v-model="conclusionText"
          :value="conclusion.conclusion"
        >
        </v-textarea>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn small text @click="editable = false"> Cancel </v-btn>
          <v-btn small text color="primary" @click="saveConclusion()" :disabled="!conclusionText"> Save </v-btn>
        </v-card-actions>
      </div>
      <div v-else style="font-size: 0.9em">{{ conclusion.conclusion }}</div>

      <div v-if="showControls && currentUser == conclusion.user.username" style="position: absolute; top: 0; right: 0">
        <v-chip outlined style="margin-right: 10px">
          <v-btn icon small>
            <v-icon small @click="editConclusion()">mdi-square-edit-outline</v-icon>
          </v-btn>
          <v-btn icon small>
            <v-icon small @click="deleteConclusion()">mdi-trash-can-outline</v-icon>
          </v-btn>
        </v-chip>
      </div>
    </div>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  props: ['question', 'conclusion'],
  data: function () {
    return {
      conclusionText: '',
      editable: false,
      showControls: false,
      loading: false,
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
  },
  methods: {
    setActiveQuestion(question) {
      let payload = {
        scenario: this.activeContext.scenario,
        facet: this.activeContext.facet,
        question: question,
      }
      this.$store.dispatch('setActiveContext', payload)
    },
    saveConclusion() {
      this.loading = true
      this.editable = false
      this.showControls = false
      ApiClient.editQuestionConclusion(this.sketch.id, this.question.id, this.conclusion.id, this.conclusionText)
        .then((response) => {
          let updatedQuestion = response.data.objects[0]
          this.$store.dispatch('updateScenarios', this.sketch.id)
          this.setActiveQuestion(updatedQuestion)
          this.loading = false
        })
        .catch((e) => {
          this.loading = false
          this.editable = true
          this.errorSnackBar(e)
          console.error(e)
        })
    },
    editConclusion() {
      this.conclusionText = this.conclusion.conclusion
      this.editable = true
    },
    deleteConclusion(conclusion) {
      this.loading = true
      if (confirm('Are you sure?')) {
        ApiClient.deleteQuestionConclusion(this.sketch.id, this.question.id, this.conclusion.id)
          .then((response) => {
            let updatedQuestion = response.data.objects[0]
            this.$store.dispatch('updateScenarios', this.sketch.id)
            this.setActiveQuestion(updatedQuestion)
            this.loading = false
          })
          .catch((e) => {})
      } else {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped lang="scss"></style>
