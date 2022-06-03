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
  <v-simple-table>
    <template v-slot:default>
      <thead>
        <tr>
          <th class="text-left">Search history</th>
          <th class="text-left">Count</th>
          <th class="text-left">Query time</th>
          <th class="text-left">Date</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="search in searchHistory" :key="search">
          <td>
            <router-link :to="{ name: 'Explore', query: { q: search.query_string } }">
              {{ search.query_string }}
            </router-link>
          </td>
          <td>{{ search.query_result_count | compactNumber }}</td>
          <td>{{ search.query_time }}ms</td>
          <td>{{ search.created_at }}</td>
        </tr>
      </tbody>
    </template>
  </v-simple-table>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

export default {
  props: [],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  data() {
    return {
      searchHistory: [],
    }
  },
  methods: {
    fetchHistory() {
      ApiClient.getSearchHistory(this.sketch.id)
        .then((response) => {
          this.searchHistory = response.data.objects
        })
        .catch((e) => {})
    },
  },
  created: function () {
    this.fetchHistory()
  },
}
</script>
