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
          <th class="text-left">Data type</th>
          <th class="text-left">Count</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="dataType in dataTypes" :key="dataType.data_type">
          <td>
            <router-link :to="{ name: 'Explore', query: { q: 'data_type:&quot;' + dataType.data_type + '&quot;' } }">
              {{ dataType.data_type }}
            </router-link>
          </td>
          <td>{{ dataType.count | compactNumber }}</td>
        </tr>
      </tbody>
    </template>
  </v-simple-table>
</template>

<script>
export default {
  props: [],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    dataTypes() {
      return this.$store.state.dataTypes
    },
  },
  data() {
    return {}
  },
  methods: {},
}
</script>
