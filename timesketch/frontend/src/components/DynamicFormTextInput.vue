<!--
Copyright 2019 Google Inc. All rights reserved.

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
  <div class="field">
    <p class="control">
      <input class="input"
        type="text"
        :name="name"
        :value="value"
        :placeholder="placeholder"
        @input="$emit('input', $event.target.value)">
    </p>
  </div>
</template>
<script>
export default {
  name: 'ts-dynamic-form-text-input',
  props: ['placeholder', 'name', 'value']
}
</script>

<style lang="scss"></style>
