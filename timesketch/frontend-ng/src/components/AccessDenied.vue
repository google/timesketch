<!--
Copyright 2026 Google Inc. All rights reserved.

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
  <v-container fill-height fluid>
    <v-row align="center" justify="center">
      <v-sheet class="pa-4" style="background: transparent">
        <div class="text-center">
          <v-icon size="80" color="grey">mdi-lock</v-icon>
          <div style="font-size: 2em" class="mb-3 mt-3">Access Denied</div>
          <div class="mb-5 text--secondary">
            You don't have permission to access this sketch.<br />
            Contact the sketch owner to request access.
          </div>
          <v-btn rounded depressed color="primary" to="/">
            <v-icon left>mdi-home</v-icon>
            Go to Home
          </v-btn>
        </div>
      </v-sheet>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'TsAccessDenied',
}
</script>
