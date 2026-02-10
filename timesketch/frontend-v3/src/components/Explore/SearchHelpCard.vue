<!--
Copyright 2025 Google Inc. All rights reserved.

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
  <SearchGuideCard
    :flat="flat"
    :show-tags="false"
    :show-data-types="false"
    :show-saved-searches="false"
    @search-triggered="$emit('close-dialog')"
  >
    <template v-slot:header>
      <div class="pa-4 pb-0">
        <v-card-title class="d-flex align-center">
          <v-icon large start>mdi-file-search-outline</v-icon>
          Search Examples and Query Guide
          <v-spacer></v-spacer>
          <v-btn v-if="flat" variant="text" icon="mdi-close" @click="$emit('close-dialog')" title="Close dialog"> </v-btn>
        </v-card-title>
        <v-card-subtitle class="mt-2 mb-2"> Find below some examples on how to explore your data. </v-card-subtitle>
        <v-divider></v-divider>
      </div>
    </template>
  </SearchGuideCard>
</template>

<script>

export default {
  name: 'SearchHelpCard',
  props: {
    flat: {
      type: Boolean,
      default: false,
    },
  },
}
</script>
