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
  <v-skeleton-loader
    type="list-item"
    height="48"
    width="180"
    class="ma-0"
  ></v-skeleton-loader>
  <div class="d-flex" v-for="(_, index) in 5">
    <v-skeleton-loader
      type="list-item"
      height="48"
      width="62"
      class="ma-0"
    ></v-skeleton-loader
    ><v-skeleton-loader
      type="list-item"
      height="44"
      :width="randomWidth(index)"
      class="ma-0"
    ></v-skeleton-loader>
  </div>
</template>

<script>
export default {
  methods: {
    randomWidth(index) {
      const minuend = 450;
      const subtrahend = Math.random() * (index * 20);

      return minuend - subtrahend;
    },
  },
};
</script>
