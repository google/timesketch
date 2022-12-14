<!--
Copyright 2022 Google Inc. All rights reserved.

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
  <v-card>
    <v-card-title>Share sketch</v-card-title>
    <v-card-text>
      <v-radio-group v-model="column" column>
        <v-radio label="Private - Only you and selected users/groups can access this sketch" value="radio-1"></v-radio>
        <v-radio label="Public - All users of the system can access this sketch" value="radio-2"></v-radio>
      </v-radio-group>
    </v-card-text>
  </v-card>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

export default {
  data() {
    return {}
  },
  methods: {},
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
