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
  <div style="font-size: 0.9em">
    <div
      class="pb-4 markdown-body"
      style="font-size: 1em; background-color: transparent"
      v-html="toHtml(approach.description.details)"
    ></div>

    <div v-if="opensearchQueries.length" class="pb-4">
      <strong>Suggested queries</strong>
      <ts-search-chip
        v-for="opensearchQuery in opensearchQueries"
        :key="opensearchQuery.value"
        :searchchip="opensearchQuery"
        type="link"
        class="mb-1"
      ></ts-search-chip>
    </div>

    <span style="cursor: pointer" @click="showDetails = !showDetails">
      <v-icon v-if="!showDetails" color="primary" small>mdi-chevron-right</v-icon>
      <v-icon v-else small>mdi-chevron-down</v-icon>
      <small style="color: #1976d2">More info..</small>
    </span>

    <v-expand-transition>
      <div v-if="showDetails" class="mt-3">
        <!-- References -->
        <div v-if="approach.description.references && approach.description.references.length">
          <v-icon class="mr-2">mdi-link-variant</v-icon>
          <strong>References</strong>
          <ul class="mb-4 mt-2 markdown-body" style="line-height: 70%; background-color: transparent">
            <li v-for="reference in approach.description.references" :key="reference">
              <div v-html="toHtml(reference)" style="font-size: 0.9em"></div>
            </li>
          </ul>
        </div>

        <v-sheet style="max-width: 80%; background-color: transparent" class="mb-3">
          <v-icon color="success" class="mr-2">mdi-check</v-icon>
          <strong>Covered</strong>
          <ul class="mt-2">
            <li v-for="note in approach._view.notes.covered" :key="note">{{ note }}</li>
          </ul>
        </v-sheet>

        <v-sheet style="max-width: 80%; background-color: transparent">
          <v-icon color="error" class="mr-2">mdi-close</v-icon>
          <strong>Not covered</strong>
          <ul class="mt-2">
            <li v-for="note in approach._view.notes.not_covered" :key="note">{{ note }}</li>
          </ul>
        </v-sheet>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import TsSearchChip from './SearchChip.vue'

export default {
  props: ['approachJSON'],
  components: { TsSearchChip },
  data: function () {
    return {
      showDetails: false,
    }
  },
  computed: {
    approach() {
      return JSON.parse(this.approachJSON.spec_json)
    },
    opensearchQueries() {
      let opensearchQueries = []
      this.approach._view.processors.forEach((processor) => {
        processor.analysis.forEach((analysis) => {
          if (analysis.name === 'OpenSearch') {
            analysis.steps.forEach((step) => {
              if (step.type === 'opensearch-query') {
                opensearchQueries.push(step)
              }
            })
          }
        })
      })
      return opensearchQueries
    },
  },
  methods: {
    toHtml(markdown) {
      return DOMPurify.sanitize(marked(markdown))
    },
  },
}
</script>

