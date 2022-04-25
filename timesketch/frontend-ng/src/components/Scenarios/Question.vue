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
    <div style="cursor: pointer; font-size: 0.9em; font-weight: bold" class="pl-3 pt-3" @click="expanded = !expanded">
      <v-icon small v-if="!expanded">mdi-chevron-right</v-icon>
      <v-icon small v-else>mdi-chevron-down</v-icon>
      {{ question.display_name }}
    </div>
    <div style="font-size: 0.9em" class="pa-3 pl-8" v-show="expanded">
      <span>{{ question.description }}</span>
      <v-textarea disabled outlined flat hide-details auto-grow rows="3" label="Your conclusion" class="mt-4">
        <template v-slot:prepend-inner>
          <v-avatar color="grey" class="mt-n1" size="28"></v-avatar>
        </template>
      </v-textarea>
      <v-card-actions class="pl-0">
        <v-btn disabled x-small outlined color="primary"> Answer Yes </v-btn>
        <v-btn disabled x-small outlined color="primary"> Answer No </v-btn>
        <v-btn disabled x-small outlined color="primary"> Inconclusive </v-btn>
      </v-card-actions>
    </div>
  </div>
</template>

<script>
export default {
  props: ['question'],
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
