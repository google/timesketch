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
  <v-simple-table>
    <template v-slot:default>
      <thead>
        <tr>
          <th></th>
          <th class="text-left">
            Name
          </th>
          <th class="text-left">
            Description
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="analyzer in sortedAnalyzers()"
          :key="analyzer.name"
        >
        <td>
            <v-btn small depressed text color="primary">
              <v-icon small left>mdi-auto-fix</v-icon>
              Run Alayzer
            </v-btn>
          </td>
          <td>{{ analyzer.display_name}}</td>
          <td>{{ analyzer.description }}</td>
        </tr>
      </tbody>
    </template>
  </v-simple-table>
</template>

<script>
export default {
  data() {
    return {
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch;
    },
    analyzerList() {
        return this.$store.state.sketchAnalyzerList;
    },
  },
  methods: {
    // Sort alphabetically based on analyzer display_name
    sortedAnalyzers() {
      let unsortedAnalyzerList = []
      for (let analyzer in this.analyzerList) {
        unsortedAnalyzerList.push(this.analyzerList[analyzer])
      }
      let sortedAnalyzerList = [...unsortedAnalyzerList]
      sortedAnalyzerList.sort((a, b) => a.display_name.localeCompare(b.display_name))
      return sortedAnalyzerList
    },
  },
}
</script>
