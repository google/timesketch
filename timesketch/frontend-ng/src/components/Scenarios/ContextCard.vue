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
  <v-card outlined class="mt-3 mx-3" v-if="activeContext.question">
    <v-toolbar dense flat>
      <strong>{{ activeContext.question.display_name }}</strong>
      <v-spacer></v-spacer>
      <v-btn small icon @click="$store.dispatch('clearActiveContext')" class="mr-1">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-toolbar>
    <v-divider></v-divider>
    <div class="pa-4 markdown-body" v-html="toHtml(activeContext.question.description)" style="font-size: 0.9em"></div>
  </v-card>
</template>

<script>
import DOMPurify from 'dompurify'
import { marked } from 'marked'

export default {
  computed: {
    activeContext() {
      return this.$store.state.activeContext
    },
  },
  methods: {
    toHtml(markdown) {
      return DOMPurify.sanitize(marked(markdown))
    },
  },
}
</script>

