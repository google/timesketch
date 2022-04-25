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
    <v-row style="cursor: pointer" @click="expanded = !expanded" class="pa-3 pb-0 pl-0">
      <v-col cols="1">
        <v-btn icon>
          <v-icon v-if="!expanded">mdi-chevron-right</v-icon>
          <v-icon v-else>mdi-chevron-down</v-icon>
        </v-btn>
      </v-col>
      <v-col cols="9">
        <span style="font-size: 0.9em">{{ facet.display_name }}</span>
      </v-col>
      <v-col cols="2">
        <v-chip color="orange" small> 3/5 </v-chip>
      </v-col>
    </v-row>

    <div v-show="expanded">
      <span style="font-size: 0.9em" v-for="question in facet.questions" :key="question.id">
        <ts-question :question="question"></ts-question>
      </span>
    </div>
    <v-btn v-show="expanded" small text color="primary" class="ml-1 mt-3 mb-2">+ Question</v-btn>
    <v-divider class="mt-3"></v-divider>
  </div>
</template>

<script>
import TsQuestion from './Question'

export default {
  props: ['facet'],
  components: { TsQuestion },
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
