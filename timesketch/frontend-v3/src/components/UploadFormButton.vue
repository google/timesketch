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
  <ts-upload-timeline-form>
    <template v-slot="slotProps">
      <v-btn v-if="btnType === 'small'" small text rounded color="primary" v-bind="slotProps">
        <v-icon left small> mdi-plus </v-icon>
        Add Timeline
      </v-btn>
      <v-btn v-else rounded depressed color="primary" v-bind="slotProps">
        <v-icon left> mdi-plus </v-icon>
        Add Timeline
      </v-btn>
    </template>
  </ts-upload-timeline-form>
</template>
<script>

import TsUploadTimelineForm from './UploadForm.vue'

export default {
  props: ['btnType'],
  components: {
    TsUploadTimelineForm,
  },
}
</script>
