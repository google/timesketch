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
    <v-list lines="three">
      <v-list-item @mouseover="showControls = true" @mouseleave="showControls = false">
        
          <v-list-item-title style="font-size: 0.9em">
            <strong>{{ conclusion.user.username }}</strong>
          </v-list-item-title>
          <v-list-item-subtitle>
            <small>{{ conclusion.created_at | shortDateTime }} ({{ conclusion.created_at | timeSince }})</small>
          </v-list-item-subtitle>

          <div v-if="editable">
            <v-textarea
              style="font-size: 0.9em"
              hide-details
              auto-grow
              variant="outlined"
              v-model="conclusionText"
              :model-value="conclusion.conclusion"
            >
            </v-textarea>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn size="small" variant="text" @click="editable = false"> Cancel </v-btn>
              <v-btn size="small" variant="text" color="primary" @click="saveConclusion()" :disabled="!conclusionText"> Save </v-btn>
            </v-card-actions>
          </div>
          <div v-else style="max-width: 90%; font-size: 0.9em">{{ conclusion.conclusion }}</div>
        

        <v-list-item-action
          v-if="showControls && currentUser == conclusion.user.username"
          style="position: absolute; right: 0"
        >
          <v-chip variant="outlined" style="margin-right: 10px">
            <v-btn icon size="small">
              <v-icon size="small" @click="editConclusion()">mdi-square-edit-outline</v-icon>
            </v-btn>
            <v-btn icon size="small">
              <v-icon size="small" @click="deleteConclusion()">mdi-trash-can-outline</v-icon>
            </v-btn>
          </v-chip>
        </v-list-item-action>
      </v-list-item>
    </v-list>
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
  },
  methods: {
    saveConclusion: function () {
      this.loading = true
      this.editable = false
      this.showControls = false
      ApiClient.editQuestionConclusion(this.sketch.id, this.question.id, this.conclusion.id, this.conclusionText)
        .then((response) => {
          this.$store.dispatch('updateScenarios', this.sketch.id).then(() => {
            this.loading = false
          })
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
            this.$store.dispatch('updateScenarios', this.sketch.id).then(() => {
              this.loading = false
            })
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
