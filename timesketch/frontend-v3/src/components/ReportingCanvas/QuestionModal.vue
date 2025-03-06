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
        <div v-if="isLoading">
          <v-skeleton-loader
            type="list-item"
            height="44"
            width="220"
            class="ma-0"
          ></v-skeleton-loader>
          <div class="d-flex">
            <v-skeleton-loader
              type="list-item"
              height="44"
              width="62"
              class="ma-0"
            ></v-skeleton-loader
            ><v-skeleton-loader
              type="list-item"
              height="44"
              width="500"
              class="ma-0"
            ></v-skeleton-loader>
          </div>
          <div class="d-flex">
            <v-skeleton-loader
              type="list-item"
              height="44"
              width="62"
              class="ma-0"
            ></v-skeleton-loader
            ><v-skeleton-loader
              type="list-item"
              height="44"
              width="490"
              class="ma-0"
            ></v-skeleton-loader>
          </div>

          <div class="d-flex">
            <v-skeleton-loader
              type="list-item"
              height="44"
              width="62"
              class="ma-0"
            ></v-skeleton-loader
            ><v-skeleton-loader
              type="list-item"
              height="44"
              width="460"
              class="ma-0"
            ></v-skeleton-loader>
          </div>

          <div class="d-flex">
            <v-skeleton-loader
              type="list-item"
              height="44"
              width="62"
              class="ma-0"
            ></v-skeleton-loader
            ><v-skeleton-loader
              type="list-item"
              height="44"
              width="590"
              class="ma-0"
            ></v-skeleton-loader>
          </div>

          <div class="d-flex">
            <v-skeleton-loader
              type="list-item"
              height="44"
              width="62"
              class="ma-0"
            ></v-skeleton-loader
            ><v-skeleton-loader
              type="list-item"
              height="44"
              width="580"
              class="ma-0"
            ></v-skeleton-loader>
          </div>

          <div class="d-flex">
            <v-skeleton-loader
              type="list-item"
              height="44"
              width="62"
              class="ma-0"
            ></v-skeleton-loader
            ><v-skeleton-loader
              type="list-item"
              height="44"
              width="530"
              class="ma-0"
            ></v-skeleton-loader>
          </div>
        </div>
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
                @click="createQuestion(question)"
                class="d-flex"
              >
                <template v-slot:prepend>
                  <v-icon small class="mr-2">mdi-plus</v-icon>
                </template>
                <v-list-item-title> {{ question.name }}</v-list-item-title>
              </v-list-item>
            </div>
          </v-list>
          <v-list
            class="questions-group mb-4"
            v-if="aiMatches && aiMatches.length > 0"
          >
            <v-list-subheader class="font-weight-bold">
              AI-Suggested Questions
              <span>({{ aiMatches.length }})</span></v-list-subheader
            >
            <div class="questions-group__list overflow-y-auto">
              <v-list-item
                v-for="(question, index) in aiMatches"
                :key="index"
                @click="createQuestion(question)"
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

<script setup>
import { ref, onMounted } from "vue";
import { useAppStore } from "@/stores/app";
import RestApiClient from "@/utils/RestApiClient";
import { VListItem } from "vuetify/components";

const store = useAppStore();
const emit = defineEmits(["close-modal"]);
const addNewQuestion = inject("addNewQuestion");

onMounted(() => {
  fetchQuestionTemplates();
});

const isLoading = ref(true);
const queryString = ref(null);
const dfiqTemplates = ref([]);
const aiTemplates = ref([]);

const fetchQuestionTemplates = async () => {
  try {
    const [dfiqTemplatesRes, aiTemplatesRes] = await Promise.all([
      await RestApiClient.getQuestionTemplates(),
      await RestApiClient.getQuestionTemplates(), // TODO - replace with ai request
    ]);

    if (aiTemplatesRes.data.objects && aiTemplatesRes.data.objects.length > 0) {
      aiTemplates.value = aiTemplatesRes.data.objects.splice(1, 4);
    }

    if (
      dfiqTemplatesRes.data.objects &&
      dfiqTemplatesRes.data.objects.length > 0
    ) {
      dfiqTemplates.value = dfiqTemplatesRes.data.objects;
    }
  } catch (error) {
  } finally {
    isLoading.value = false;
  }
};

const aiMatches = computed(() => {
  if (!queryString.value) {
    return aiTemplates.value;
  }

  return aiTemplates.value.filter((template) =>
    template.name.toLowerCase().includes(queryString.value.toLowerCase())
  );
});

const dfiqMatches = computed(() => {
  if (!queryString.value) {
    return [];
  }

  return dfiqTemplates.value.filter((template) =>
    template.name.toLowerCase().includes(queryString.value.toLowerCase())
  );
});

const isSubmitting = ref(false);
const createQuestion = async (template = null) => {
  if (!store.sketch) {
    return;
  }

  isSubmitting.value = true;

  let questionText = queryString;
  let templateId = null;

  if (template !== null) {
    questionText = template.name;
    templateId = template.id;
  }

  try {
    const question = await RestApiClient.createQuestion(
      store.sketch.id,
      null,
      null,
      questionText.value,
      templateId
    );

    addNewQuestion(question.data.objects[0]);

    emit("close-modal");

    store.setNotification({
      text: `You added the question "${question.data.objects[0].name}" to this Sketch`,
      icon: "mdi-plus-circle-outline",
      type: "success",
    });
  } catch (error) {
    store.setNotification({
      text: "Unable to add question to this Sketch. Please try again.",
      icon: "mdi-alert-circle-outline",
      type: "error",
    });
  } finally {
    isSubmitting.value = false;
  }
};
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
  height: 200px;
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
