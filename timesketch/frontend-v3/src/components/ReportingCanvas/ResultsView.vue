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
  <section>
    <header class="pb-8 mb-8 border-b-thin">
      <h2 class="mb-4 text-h5 font-weight-bold">Results</h2>
    </header>
    
    {{ question.name }}
  </section>
</template>

<script setup>
const { question } = defineProps({
  question: Object
});
</script>

<style scoped>
.questions-list {
    list-style: none;
}

.question::marker {
  font-size: inherit;
  font-weight: inherit;
}
</style>
