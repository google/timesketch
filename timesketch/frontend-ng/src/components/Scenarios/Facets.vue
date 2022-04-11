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
    <v-sheet style="cursor: pointer" @click="expanded = !expanded" class="pa-4 pb-0 pl-0">
      <v-btn icon>
        <v-icon v-if="!expanded">mdi-chevron-right</v-icon>
        <v-icon v-else>mdi-chevron-down</v-icon>
      </v-btn>
      <b>{{ facet.display_name }}</b>
    </v-sheet>

    <v-sheet v-show="expanded">
      <v-sheet class="pa-3 pb-0 pl-4" style="font-size: 0.9em" v-for="question in facet.questions" :key="question.id">
        <ts-questions :question="question"></ts-questions>
      </v-sheet>
    </v-sheet>
  </div>
</template>

<script>
import TsQuestions from './Questions'

export default {
  props: ['facet'],
  components: { TsQuestions },
  data: function () {
    return {
      expanded: false,
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
