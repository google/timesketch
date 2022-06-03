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
          <th class="text-left">Name</th>
          <th class="text-left">Created</th>
          <th class="text-left">Uploaded by</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="timeline in activeTimelines" :key="timeline.id">
          <td>
            <v-avatar rounded :color="'#' + timeline.color" size="24" class="mr-2"> </v-avatar>

            <router-link :to="{ name: 'Explore', query: { timeline: timeline.id } }">
              {{ timeline.name }}
            </router-link>
          </td>
          <td>{{ timeline.created_at }}</td>
          <td>{{ timeline.user.username }}</td>
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
    activeTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.active_timelines]
      return timelines.sort(function (a, b) {
        return a.name.localeCompare(b.name)
      })
    },
  },
  data() {
    return {}
  },
  methods: {},
}
</script>
