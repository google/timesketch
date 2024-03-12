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
  <div @mouseover="showControls = true" @mouseleave="showControls = false" style="position: relative">
    <div style="font-size: 0.9em" class="mb-4">
      <strong>{{ conclusion.user.username }}</strong>
      <small class="ml-3">{{ conclusion.created_at | shortDateTime }} ({{ conclusion.created_at | timeSince }})</small>
    </div>

    <div v-if="editable">
      <v-textarea
        style="font-size: 0.9em"
        outlined
        flat
        hide-details
        auto-grow
        rows="3"
        clearable
        v-model="conclusionText"
        :value="conclusion.conclusion"
      >
      </v-textarea>
      <v-card-actions>
        <v-btn small text color="primary" @click="saveConclusion()" :disabled="!conclusionText"> Save </v-btn>
        <v-btn small text @click="editable = false"> Cancel </v-btn>
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
    saveConclusion() {
      this.editable = false
      this.showControls = false
      ApiClient.editQuestionConclusion(this.sketch.id, this.question.id, this.conclusion.id, this.conclusionText)
        .then((response) => {
          this.$emit('save-conclusion')
        })
        .catch((e) => {
          this.editable = true
          this.errorSnackBar(e)
          console.error(e)
        })
    },
    editConclusion() {
      this.conclusionText = this.conclusion.conclusion
      this.editable = true
    },
    deleteConclusion() {
      if (confirm('Are you sure?')) {
        this.$emit('delete')
      }
    },
  },
}
</script>

<style scoped lang="scss"></style>
