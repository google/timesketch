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
  <div>
    <div class="buttons">
      <b-tooltip
        :label="node.query_string"
        type="is-light"
        position="is-bottom"
        multilined
        v-for="node in searchHistory"
        :key="node.id"
      >
        <button class="button" v-on:click="selectHistoryNode(node)" style="margin-right:7px;">
          <span class="query-string" v-if="node.query_string !== '*'">{{ node.query_string }}</span>
          <span v-if="node.query_string === '*'">Everything</span>
          <b-tag style="margin-left:7px;">{{ node.query_result_count | compactNumber }}</b-tag>
        </button>
      </b-tooltip>
    </div>
  </div>
</template>

<script>
import EventBus from '../../main'

export default {
  data() {
    return {
      history: [],
    }
  },
  props: ['limit'],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    searchHistory() {
      return this.$store.state.searchHistory
    },
  },
  methods: {
    selectHistoryNode(node) {
      this.$emit('node-click', node)
      this.$emit('close-on-click')
      EventBus.$emit('selected-node-from-dropdown', node)
    },
  },
  created: function() {
    // this.$store.dispatch('updateSearchHistory')
  },
}
</script>

<style scoped lang="scss">
.query-string {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
  word-wrap: break-word;
  color: var(--font-color-dark);
}
</style>
