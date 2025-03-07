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
  <section>
    <header class="report-header px-6 pt-8 mb-6">
      <h2 class="mb-4 text-h5 font-weight-bold">Results</h2>
      <v-card
        color="#3874CB"
        :variant="variant"
        class="mb-6 d-flex align-center justify-space-between pa-2"
      >
        <v-card-item>
          <div>
            <div class="text-overline mb-1">
              {{ variant }}
            </div>
            <p class="text-body-1 font-weight-medium">
              Would you like to save the results to the report?
            </p>
          </div>
        </v-card-item>

        <v-card-actions>
          <v-btn>Remove Question</v-btn>
          <v-btn rounded variant="flat" color="#ffffff"
            >Confirm &amp; Save</v-btn
          >
        </v-card-actions>
      </v-card>
      <h1 class="mb-4 text-h4 font-weight-bold">{{ question.name }}</h1>
    </header>

    <div class="px-6 mb-8">
      <div class="d-flex justify-space-between">
        <label for="conclusion" class="text-h6 font-weight-bold d-block mb-2"
          >Conclusion</label
        >
      </div>
      <v-textarea
        hide-details="auto"
        id="conclusion"
        name="conclusion"
        variant="outlined"
        class="mb-2"
      ></v-textarea>
      <v-btn
        variant="text"
        size="small"
        color="primary"
        class="text-uppercase pa-0"
      >
        <v-icon icon="mdi-reload" left small class="mr-1" />
        Regenerate Conclusion</v-btn
      >
    </div>
    <div class="px-6">
      <h3 class="text-h6 font-weight-bold mb-5">Key Observables</h3>
      <v-expansion-panels v-model="panelA" class="mb-6">
        <v-expansion-panel
          title="Potential Malware Detected"
          text="The /usr/bin/dhpcd file is flagged as a high-risk executable based on Yara rule matches (executables_ELF) and multiple security tags."
        >
        <!-- <EventsList
        :query-request="activeQueryRequest"
        @countPerIndex="updateCountPerIndex($event)"
        @countPerTimeline="updateCountPerTimeline($event)"
      ></EventsList> -->
        </v-expansion-panel>
      </v-expansion-panels>
      <v-expansion-panels v-model="panelB">
        <v-expansion-panel
          title="Multiple Event Correlation"
          text="The file appears in several security events (177-193, 52-55), indicating widespread presence across the system."
        >
        </v-expansion-panel>
      </v-expansion-panels>
    </div>
  </section>
</template>

<script setup>
import EventsList from '../EventsList.vue';

const { question } = defineProps({
  question: Object,
});

const panelA = ref([0]);
const panelB = ref([]);
</script>

<style scoped>
.questions-list {
  list-style: none;
}

.question::marker {
  font-size: inherit;
  font-weight: inherit;
}
</style>
