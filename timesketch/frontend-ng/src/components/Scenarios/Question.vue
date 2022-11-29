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
    <v-row
      no-gutters
      class="pa-2 pl-4"
      @click="expanded = !expanded"
      style="cursor: pointer; font-size: 0.9em"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <v-col cols="1">
        <v-icon small v-if="!expanded">mdi-chevron-right</v-icon>
        <v-icon small v-else>mdi-chevron-down</v-icon>
      </v-col>
      <v-col cols="11">
        {{ question.display_name }}
      </v-col>
    </v-row>

    <v-expand-transition>
      <div v-show="expanded">
        <div class="ma-2 mx-4 mb-4 mt-n1">
          <div v-if="fullDescription">
            <small>{{ question.description }} <a @click="fullDescription = !fullDescription">show less</a></small>
          </div>
          <div v-if="!fullDescription">
            <span>
              <small>
                {{ question.description.slice(0, 100) }}...
                <a @click="fullDescription = !fullDescription">show more</a>
              </small>
            </span>
          </div>
        </div>

        <div v-if="question.search_templates.length" flat class="ma-2 mx-4 mb-6">
          <strong><small>Query suggestions</small></strong>
          <div v-for="searchtemplate in question.search_templates" :key="searchtemplate.id" class="pa-1 mt-1">
            <ts-search-template :searchtemplate="searchtemplate"></ts-search-template>
          </div>
        </div>

        <div style="font-size: 0.9em" class="pa-4 pt-0">
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
              <v-avatar color="grey" class="mt-n2 mr-2" size="28"></v-avatar>
            </template>
          </v-textarea>
          <v-expand-transition>
            <div v-if="conclusionText">
              <v-card-actions class="pr-0">
                <v-spacer></v-spacer>
                <v-btn small text @click="conclusionText = ''"> Cancel </v-btn>
                <v-btn small text color="primary" @click="saveConclusion"> Save </v-btn>
              </v-card-actions>
            </div>
          </v-expand-transition>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import TsSearchTemplate from '../LeftPanel/SearchTemplateCompact.vue'

export default {
  props: ['question'],
  components: {
    TsSearchTemplate,
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
  },
  methods: {
    saveConclusion: function () {},
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
