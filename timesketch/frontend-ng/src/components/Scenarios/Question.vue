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
    <div class="pl-6" @click="expanded = !expanded" style="cursor: pointer; font-size: 0.9em">
      <div :class="[$vuetify.theme.dark ? 'dark-hover' : 'light-hover']" class="pa-2 mr-3" style="border-radius: 6px">
        <strong v-if="!question.conclusions.length">{{ question.display_name }}</strong>
        <span v-else>{{ question.display_name }}</span>
      </div>
    </div>

    <v-expand-transition>
      <div v-show="expanded">
        <!-- Query suggestions -->
        <div class="pa-2 pl-9">
          <v-icon x-small class="mr-1">mdi-magnify</v-icon>
          <strong><small>Query suggestions</small></strong>
          <div v-for="searchtemplate in searchTemplates" :key="searchtemplate.id" class="pa-1 mt-1">
            <ts-search-template :searchtemplate="searchtemplate"></ts-search-template>
          </div>
        </div>

        <!-- Conclusions -->
        <div class="mb-3 pl-9">
          <v-icon x-small class="mr-1">mdi-check-circle-outline</v-icon>
          <strong><small>Conclusions</small></strong>
          <v-sheet outlined rounded class="mt-2 mr-3" v-for="conclusion in question.conclusions" :key="conclusion.id">
            <ts-question-conclusion :question="question" :conclusion="conclusion"></ts-question-conclusion>
          </v-sheet>
        </div>

        <!-- Add new conclusion -->
        <div v-if="!currentUserConclusion" style="font-size: 0.9em" class="pb-2 pl-9 mr-3">
          <v-textarea
            v-model="conclusionText"
            outlined
            flat
            hide-details
            auto-grow
            rows="1"
            placeholder="Add your conclusion..."
            style="font-size: 0.9em"
          >
            <template v-slot:prepend-inner>
              <v-avatar color="grey" class="mt-n2 mr-2" size="28">
                <span class="white--text">{{ currentUser | initialLetter }}</span>
              </v-avatar>
            </template>
          </v-textarea>
          <v-expand-transition>
            <div v-if="conclusionText">
              <v-card-actions class="pr-0">
                <v-spacer></v-spacer>
                <v-btn small text @click="conclusionText = ''"> Cancel </v-btn>
                <v-btn small text color="primary" @click="createConclusion()"> Save </v-btn>
              </v-card-actions>
            </div>
          </v-expand-transition>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsSearchTemplate from '../LeftPanel/SearchTemplateCompact'
import TsQuestionConclusion from './QuestionConclusion'

export default {
  props: ['question'],
  components: {
    TsSearchTemplate,
    TsQuestionConclusion,
  },
  data: function () {
    return {
      expanded: false,
      fullDescription: false,
      conclusionText: '',
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    currentUser() {
      return this.$store.state.currentUser
    },
    searchTemplates() {
      return this.question.approaches.map((approach) => approach.search_templates).flat()
    },
    currentUserConclusion() {
      return this.question.conclusions.filter((conclusion) => conclusion.user.username === this.currentUser).length
    },
  },
  methods: {
    createConclusion: function () {
      ApiClient.createQuestionConclusion(this.sketch.id, this.question.id, this.conclusionText)
        .then((response) => {
          this.conclusionText = ''
          this.$store.dispatch('updateScenarios', this.sketch.id)
        })
        .catch((e) => {})
    },
  },
  created() {},
}
</script>

<style scoped lang="scss">
.description-ellipsis {
  width: 500px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
