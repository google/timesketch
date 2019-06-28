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
    <div class="control">
      <div class="select">
        <select :value="value" @input="$emit('input', $event.target.value)">
          <option v-for="option in options" :key="option">
            {{ option }}
          </option>
        </select>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ts-dynamic-form-radio-input',
  props: ['options', 'label', 'value']
}
</script>

<style lang="scss"></style>
