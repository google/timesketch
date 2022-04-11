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
  <v-sheet>
    <span style="cursor: pointer" @click="expanded = !expanded">
      <v-icon small color="green" class="mr-1">mdi-check</v-icon>
      {{ question.display_name }}
    </span>
    <v-card flat class="pa-3" v-show="expanded" filled>
      {{ question.description }}
      <v-card-actions class="pl-0">
        <v-btn small text color="primary" class="pl-0"> Mark complete </v-btn>
      </v-card-actions>
    </v-card>
  </v-sheet>
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
