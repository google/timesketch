<!--
Copyright 2024 Google LLC

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
  <v-data-table :loading="loading" :items="sketches"></v-data-table>
</template>

<script>
import ApiClient from "@/utils/RestApiClient";

export default {
  data() {
    return {
      sketches: [],
      loading: false,
    };
  },
  methods: {
    getSketches: function () {
      this.loading = true;
      ApiClient.getSketchList("user", 1, 10)
        .then((response) => {
          this.sketches = response.data.objects;
          this.loading = false;
        })
        .catch((e) => {
          this.loading = false;
          console.error(e);
        });
    },
  },
  mounted() {
    this.getSketches();
  },
};
</script>
