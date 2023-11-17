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
  <div style="font-size: 0.9em">
    <div
      class="pb-4 markdown-body"
      style="font-size: 1em; background-color: transparent"
      v-html="toHtml(approach.description.details)"
    ></div>

    <div v-if="approach.description.references && approach.description.references.length">
      <v-icon class="mr-2">mdi-link-variant</v-icon>
      <strong>References</strong>
      <ul class="mb-4 mt-2 markdown-body" style="line-height: 70%; background-color: transparent">
        <li v-for="reference in approach.description.references" :key="reference">
          <div v-html="toHtml(reference)" style="font-size: 0.9em"></div>
        </li>
      </ul>
    </div>

    <v-sheet style="max-width: 80%" class="mb-3">
      <v-icon color="success" class="mr-2">mdi-check</v-icon>
      <strong>Covered</strong>
      <ul class="mt-2">
        <li v-for="note in approach._view.notes.covered" :key="note">{{ note }}</li>
      </ul>
    </v-sheet>

    <v-sheet style="max-width: 80%">
      <v-icon color="error" class="mr-2">mdi-close</v-icon>
      <strong>Not covered</strong>
      <ul class="mt-2">
        <li v-for="note in approach._view.notes.not_covered" :key="note">{{ note }}</li>
      </ul>
    </v-sheet>
  </div>
</template>

<script>
import DOMPurify from 'dompurify'
import { marked } from 'marked'

export default {
  props: ['approachJSON'],
  data: function () {
    return {
      showDetails: true,
      processorTab: null,
    }
  },
  computed: {
    approach() {
      return JSON.parse(this.approachJSON.spec_json)
    },
  },
  methods: {
    toHtml(markdown) {
      return DOMPurify.sanitize(marked(markdown))
    },
  },
}
</script>

