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
  <v-card v-if="activeContext.question" class="mt-3 mx-3 pb-1" variant="outlined">
    <v-toolbar flat dense style="background-color: transparent">
      <v-btn v-if="activeContext.question.description" size="small" icon @click="expanded = !expanded" class="mr-1">
        <v-icon v-if="expanded">mdi-chevron-up</v-icon>
        <v-icon v-else>mdi-chevron-down</v-icon>
      </v-btn>

      <h4>
        {{ activeContext.question.display_name }}
        <small>
          <a :href="getDfiqQuestionUrl(activeContext.question.dfiq_identifier)" target="_blank" rel="noreferrer"
            >({{ activeContext.question.dfiq_identifier }})</a
          >
        </small>
      </h4>
      <v-spacer></v-spacer>

      <v-btn size="small" icon @click="$store.dispatch('clearActiveContext')" class="mr-1">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-toolbar>
    <v-divider v-show="expanded"></v-divider>

    <v-expand-transition>
      <div v-show="expanded">
        <div v-if="activeContext.question.description">
          <div
            class="pa-4 markdown-body"
            style="background-color: transparent"
            v-html="toHtml(activeContext.question.description)"
          ></div>
        </div>

        <!--Suggested queries-->
        <div v-if="opensearchQueries.length" class="px-4 pb-4">
          <strong style="font-size: 0.9em">Suggested queries</strong>
          <ts-search-chip
            v-for="opensearchQuery in opensearchQueries"
            :key="opensearchQuery.value"
            :searchchip="opensearchQuery"
            type="link"
          ></ts-search-chip>
        </div>

        <!--Approaches-->
        <div v-if="activeContext.question.approaches.length">
          <div class="px-4 pb-4">
            <v-btn variant="flat" rounded size="small" @click="showApproaches = !showApproaches">
              <span v-if="!showApproaches">Show {{ activeContext.question.approaches.length }} approaches</span>
              <span v-else>Hide {{ activeContext.question.approaches.length }} approaches</span>
            </v-btn>
          </div>
          <v-expand-transition>
            <div v-if="showApproaches">
              <v-divider></v-divider>
              <v-expansion-panels flat variant="accordion" hover>
                <v-expansion-panel
                  v-for="(approach, index) in activeContext.question.approaches"
                  :key="approach.display_name"
                >
                  <v-expansion-panel-title>
                    <span>{{ approach.display_name }}</span>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <ts-context-card-approach :approachJSON="approach"></ts-context-card-approach>
                  </v-expansion-panel-text>
                  <v-divider v-if="index != activeContext.question.approaches.length - 1"></v-divider>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>
          </v-expand-transition>
        </div>
      </div>
    </v-expand-transition>
  </v-card>
</template>

<script>
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import TsContextCardApproach from './ContextCardApproach.vue'
import TsSearchChip from './SearchChip.vue'

export default {
  components: { TsContextCardApproach, TsSearchChip },
  data: function () {
    return {
      showApproaches: false,
      expanded: true,
    }
  },
  computed: {
    activeContext() {
      return this.$store.state.activeContext
    },
    opensearchQueries() {
      const opensearchQueries = []
      const approaches = this.activeContext.question.approaches.map((approach) => JSON.parse(approach.spec_json))
      approaches.forEach((approach) => {
        approach._view.processors.forEach((processor) => {
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
      })
      return opensearchQueries
    },
  },
  methods: {
    toHtml(markdown) {
      return DOMPurify.sanitize(marked(markdown))
    },
    getDfiqQuestionUrl(id) {
      return 'https://dfiq.org/questions/' + id + '/'
    },
  },
}
</script>

