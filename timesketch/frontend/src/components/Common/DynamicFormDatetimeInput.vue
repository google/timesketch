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
  <div class="field" v-if="display">
    <label class="label">{{ label }}</label>
    <b-datetimepicker
      placeholder="Optional: Select a date..."
      :datetime-formatter="dateFormatter"
      editable
    ></b-datetimepicker>
  </div>
</template>
<script>
export default {
  props: ['placeholder', 'label', 'name', 'value', 'display'],
  methods: {
    dateFormatter(dt) {
      // Output whatever datetime string that the user chooses in the datetime picket widget.
      // The calculations here are to match the users local timezone setting as that is what is used in the widget.
      let dateString = new Date(dt.getTime() - dt.getTimezoneOffset() * 60000).toISOString().replace('.000Z', '')
      this.$emit('input', dateString)
      return dateString
    },
  },
}
</script>
