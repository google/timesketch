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
    <div v-on:click="setActiveView(view)" v-for="view in views" :key="view.id" class="view-list-item">
      {{ view.name }}
    </div>
  </div>
</template>

<script>
export default {
  props: ['views'],
  methods: {
    setActiveView: function(view, doSearch = true) {
      if (doSearch) {
        this.$emit('setActiveView', view)
      }
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.view-list-item {
  cursor: pointer;
  padding: 5px 0 5px 0;
}
.view-list-item:hover {
  background-color: var(--table-row-hover-background-color);
}
</style>
