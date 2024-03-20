<!--
 Copyright 2024 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 -->

<template>
  <v-autocomplete
    v-bind="$attrs"
    v-model="selectedSavedSearch"
    :items="allSavedSearches"
    clearable
    outlined
    label="Select a saved search"
    @input="$emit('updateSavedSearch', $event)"
  >
  </v-autocomplete>
</template>

<script>
export default {
  props: {
    savedSearch: {
      type: Object,
    }
  },
  data() {
    return {
      selectedSavedSearch: undefined,
    }
  },
  computed: {
    allSavedSearches() {
      let savedSearches = this.$store.state.meta.views.map(
        (view) => { return {text: view['name'], value: view} }
      )
      return savedSearches
    },

  }
}
</script>
