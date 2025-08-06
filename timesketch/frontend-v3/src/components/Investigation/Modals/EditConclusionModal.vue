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
  <v-container fluid class="modal pa-8 rounded-lg">
    <ModalLoader :isSubmitting="isSubmitting" />
    <div :class="{ 'no-pointer-events': isSubmitting }">
      <h3 class="mb-4">{{ headline }}</h3>
      <v-textarea
        v-model="editedText"
        variant="outlined"
        rows="5"
        autofocus
        hide-details
      ></v-textarea>
      <div class="d-flex align-center justify-end ga-4 pa-4 mt-4">
        <v-btn
          variant="text"
          size="small"
          color="primary"
          @click="$emit('close-modal')"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          @click="editConclusion()"
          :disabled="!isChanged"
        >
          Save Changes
        </v-btn>
      </div>
    </div>
  </v-container>
</template>

<script>
import { useAppStore } from "@/stores/app";
import RestApiClient from "@/utils/RestApiClient";

export default {
  props: {
    headline: {
      type: String,
      default: true,
    },
    conclusion: {
      type: Object,
      required: true,
    },
    question: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      store: useAppStore(),
      isSubmitting: false,
      editedText: this.conclusion.conclusion,
    };
  },
  computed: {
    isChanged() {
        return this.conclusion.conclusion !== this.editedText && this.editedText.trim() !== '';
    },
    isEditMode() {
      return this.conclusion && this.conclusion.id
    },
  },
  methods: {
    async editConclusion() {
      this.isSubmitting = true
      if (this.isEditMode) {
        try {
          const response = await RestApiClient.editQuestionConclusion(
            this.store.sketch.id,
            this.question.id,
            this.conclusion.id,
            this.editedText
          )
          this.$emit("close-modal")
        } catch(e) {
            console.error(e)
        } finally {
          this.isSubmitting = false
        }
      } else {
        try {
          const response = await RestApiClient.createQuestionConclusion(
          this.store.sketch.id,
          this.question.id,
          this.editedText
        )
          this.$emit("close-modal")
        } catch(e) {
            console.error(e)
        } finally {
          this.isSubmitting = false
        }
      }
    },
  },
};
</script>

<style scoped>
.modal {
  width: 600px;
  background-color: #fff;
}
.no-pointer-events {
  pointer-events: none;
}
</style>
