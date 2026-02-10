<!--
Copyright 2025 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
  <v-skeleton-loader height="25" width="110" class="mb-8"></v-skeleton-loader>
  <v-skeleton-loader height="80" class="mb-15"></v-skeleton-loader>
  <div class="d-flex justify-space-between px-2 mb-2">
    <v-skeleton-loader height="14" width="100"></v-skeleton-loader>
    <v-skeleton-loader height="14" width="120"></v-skeleton-loader>
  </div>
  <v-list class="border-thin pa-0 border-b-0 mb-6 rounded-lg">
    <v-skeleton-loader
      v-for="item in 6"
      height="100"
      class="card-spacer"
    ></v-skeleton-loader>
  </v-list>

  <div class="d-flex flex-column align-center">
    <v-skeleton-loader height="8" class="mb-3 w-100"></v-skeleton-loader>
    <v-skeleton-loader height="8" width="250" class="mb-5"></v-skeleton-loader>
    <v-skeleton-loader height="10" width="150"></v-skeleton-loader>
  </div>
</template>

<style>
.card-spacer {
  margin-bottom: 1px;
}
</style>
