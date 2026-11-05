<!--
Copyright 2026 Google Inc. All rights reserved.

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
  <v-card outlined class="mx-3 mt-3">
    <v-alert type="error" prominent text class="mb-0">
      <div class="text-h6 mb-2">{{ language.toUpperCase() }} Query Failed</div>
      <div style="white-space: pre-wrap; font-family: monospace; font-size: 0.9em">{{ errorMessage }}</div>
      <v-divider class="my-3"></v-divider>
      <div class="text-body-2">
        <strong>Suggestions:</strong>
        <ul class="mt-1">
          <li v-if="language === 'ppl'">Just type your PPL pipe commands &mdash; the index is added automatically.</li>
          <li v-if="language === 'ppl'">Example: <code>where message LIKE '%error%' | head 100</code></li>
          <li v-if="language === 'ppl'">Example: <code>stats count() by data_type</code></li>
          <li v-if="language === 'sql'">Just type your SELECT query &mdash; the FROM clause is added automatically.</li>
          <li v-if="language === 'sql'">Example: <code>SELECT datetime, message WHERE message LIKE '%error%' LIMIT 100</code></li>
          <li>Check field names match your index mapping.</li>
          <li>Ensure string literals are properly quoted.</li>
        </ul>
      </div>
    </v-alert>
  </v-card>
</template>

<script>
export default {
  name: 'TsDirectQueryError',
  props: {
    error: {
      type: [String, Object],
      required: true,
    },
    language: {
      type: String,
      default: 'ppl',
    },
  },
  computed: {
    errorMessage() {
      if (typeof this.error === 'string') return this.error
      if (this.error && this.error.reason) return this.error.reason
      return JSON.stringify(this.error, null, 2)
    },
  },
}
</script>
