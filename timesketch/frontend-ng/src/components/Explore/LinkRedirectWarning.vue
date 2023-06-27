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
      <v-card-title>
        <v-icon large color="red">mdi-shield-alert-outline</v-icon>
        <span class="text-h6 ml-2">External redirect warning!</span>
      </v-card-title>
      <v-card-text>
        <div v-if="contextValue" class="mb-2">
          This action will open the link below in a new tab! Do you really
          want to send the following value to this external service?
        </div>
        <div v-else class="mb-2">
          This action will open the link below in a new tab! Do you really
          want to visit this external website?
        </div>
        <div v-if="contextValue">
          <b>Value:</b><br/>
          <code class="code">
            {{ contextValue }}
          </code>
        </div>
        <div>
          <b>External website:</b><br/>
          <code class="code">
            {{ contextUrl }}
          </code>
        </div>

      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          text
          @click="clearAndCancel"
        >
          cancel
        </v-btn>
        <v-btn
          color="primary"
          text
          :href="contextUrl"
          target="_blank"
          @click="clearAndCancel"
        >
          continue
        </v-btn>
      </v-card-actions>
    </v-card>
  </template>

  <script>
  export default {
    props: ['contextValue', 'contextUrl' ],
    methods: {
      clearAndCancel: function () {
        this.$emit('cancel')
      },
    },
  }
  </script>

  <style scoped lang="scss"></style>
