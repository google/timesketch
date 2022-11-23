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
    <div class="pa-2 pl-4" @click="expanded = !expanded" style="cursor: pointer">
      <a style="font-size: 1em">{{ question.display_name }}</a>
    </div>

    <v-expand-transition>
      <div v-show="expanded">
        <div class="ma-2 mx-4 mb-4 mt-n1">
          <v-expand-transition>
            <div v-if="fullDescription">
              <small>{{ question.description }} <a @click="fullDescription = !fullDescription">show less</a></small>
            </div>
          </v-expand-transition>
          <div v-if="!fullDescription">
            <span>
              <small>
                {{ question.description.slice(0, 100) }}...
                <a @click="fullDescription = !fullDescription">show more</a>
              </small>
            </span>
          </div>
        </div>

        <v-card v-if="question.search_templates.length" flat outlined class="ma-2 mx-4 mb-6">
          <v-system-bar dense flat> Get started </v-system-bar>
          <div class="pa-3">
            <ts-search-template
              v-for="searchtemplate in question.search_templates"
              :key="searchtemplate.id"
              :searchtemplate="searchtemplate"
            ></ts-search-template>
          </div>
        </v-card>

        <!-- Commented out until we have conclusion API implemented
        <div style="font-size: 0.9em" class="pa-4">
          <v-textarea
            outlined
            flat
            hide-details
            auto-grow
            rows="3"
            placeholder="Add your conclusion"
            style="font-size: 0.9em"
          >
            <template v-slot:prepend-inner>
              <v-avatar color="grey" class="mt-n2 mr-2" size="28"></v-avatar>
            </template>
          </v-textarea>
          <v-card-actions class="pl-0">
            <v-btn x-small outlined color="primary"> Yes </v-btn>
            <v-btn x-small outlined color="primary"> No </v-btn>
            <v-btn x-small outlined color="primary"> Inconclusive </v-btn>
          </v-card-actions>
        </div>
        -->
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
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  methods: {},
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
