<!--
Copyright 2025 Google Inc. All rights reserved.

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
  <v-container class="grid pa-0 fill-height" fluid>
    <v-row no-gutters class="fill-height">
      <v-col cols="4" class="bg-grey-lighten-4 pa-4 fill-height">
        <h2 class="mb-6">Questions</h2>
        <SketchProgress
          :questionsTotal="questionsTotal"
          :completedQuestionsTotal="completedQuestionsTotal"
          :percentageCompleted="percentageCompleted"
        />
        <QuestionsList
          :questions="questions"
          :questionsTotal="questionsTotal"
        />
      </v-col>
      <v-col cols="8"> </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { useAppStore } from "@/stores/app";
import RestApiClient from "@/utils/RestApiClient";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
const store = useAppStore()

const route = useRoute();

const questions = ref(null);


const questionsTotal = computed(() => questions?.value?.length);
const completedQuestionsTotal = computed(
  () => questions?.value ? questions.value.filter(({ conclusions }) => conclusions?.length > 0).length : 0
);

const percentageCompleted = computed(
  () => (completedQuestionsTotal.value / questionsTotal.value) * 100
);

watch(() => route.params.sketchId, fetchQuestions, { immediate: true });

async function fetchQuestions(id) {
  try {
    RestApiClient.getOrphanQuestions(id)
      .then((response) => {
        questions.value = response.data.objects[0];
        store.setActiveQuestion(response.data.objects[0][0].id)
      })
      .catch((e) => {
        console.error(e);
      });
  } catch (err) {
  } 
}
</script>
