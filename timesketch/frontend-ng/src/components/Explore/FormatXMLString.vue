<!--
Copyright 2021 Google Inc. All rights reserved.

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
  <v-card width="1000" style="overflow: initial">
    <v-container class="px-8">
      <v-alert border="top" colored-border type="info" elevation="2"> XML viewer </v-alert>
      <v-alert colored-border :color="'success'" border="left" elevation="1">
        <pre lang="xml">{{ xmlString }}</pre>
      </v-alert>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text color="primary" @click="clearAndCancel"> Close </v-btn>
      </v-card-actions>
    </v-container>
  </v-card>
</template>

<script>
export default {
  props: ['xmlString'],
  methods: {
    clearAndCancel: function () {
      this.$emit('cancel')
    },
  },
}
</script>

<style scoped lang="scss"></style>