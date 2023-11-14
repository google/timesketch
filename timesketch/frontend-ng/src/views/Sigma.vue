<!--
Copyright 2023 Google Inc. All rights reserved.

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
  <v-container fluid>
    <v-card flat class="mx-3">
      <ts-sigma-editor :rule-id="ruleId"></ts-sigma-editor>
    </v-card>
  </v-container>
</template>

<script>
import TsSigmaEditor from '../components/Sigma/SigmaEditor'

export default {
  props: ['ruleId'],
  components: {
    TsSigmaEditor,
  },
}
</script>
