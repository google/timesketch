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
  <span>
    <button class="button" title="Click to go back" v-on:click="searchHistoryBack" :disabled="!hasParent">
      <span class="icon is-small">
        <i class="fas fa-arrow-left"></i>
      </span>
    </button>
    <button
      class="button"
      style="padding-left:7px;"
      title="Click to go forward"
      v-on:click="searchHistoryForward"
      :disabled="!hasChild"
    >
      <span class="icon is-small">
        <i class="fas fa-arrow-right"></i>
      </span>
    </button>
  </span>
</template>

<script>
import EventBus from '../../main'

export default {
  computed: {
    currentSearchNode() {
      return this.$store.state.currentSearchNode
    },
    hasParent() {
      if (this.currentSearchNode) {
        return typeof this.currentSearchNode.parent === 'number'
      } else {
        return false
      }
    },
    hasChild() {
      if (this.currentSearchNode) {
        return this.currentSearchNode.children.length
      } else {
        return false
      }
    },
  },
  methods: {
    searchHistoryBack: function() {
      EventBus.$emit('selected-node-from-dropdown', this.currentSearchNode.parent)
    },
    searchHistoryForward: function() {
      if (!this.currentSearchNode.children.length) {
        return
      }
      let lastSearchNode = this.currentSearchNode.children.slice(-1).pop()
      EventBus.$emit('selected-node-from-dropdown', lastSearchNode)
    },
  },
}
</script>

<style scoped lang="scss">
.button {
  border: none;
  background: transparent;
}

.button[disabled] {
  background: transparent;
}
</style>
