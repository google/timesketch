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
          <th class="text-left">Tag</th>
          <th class="text-left">Events</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="tag in tags" :key="tag.tag">
          <td>
            <router-link style="text-decoration: none" :to="{ name: 'Explore', query: { q: 'tag:' + tag.tag } }">
              {{ tag.tag }}
            </router-link>
          </td>
          <td>{{ tag.count | compactNumber }}</td>
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
    meta() {
      return this.$store.state.meta
    },
    tags() {
      return this.$store.state.tags
    },
  },
  data() {
    return {}
  },
  methods: {},
}
</script>
