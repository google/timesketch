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
  <div :class="$vuetify.theme.dark ? (expanded ? 'dark-hover dark-bg' :'dark-hover') : (expanded ? 'light-hover light-bg' : 'light-hover')">
    <v-divider></v-divider>
    <div
      class="pa-2 pl-3"
      style="cursor: pointer"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? (expanded ? 'dark-hover dark-bg' :'dark-hover') : (expanded ? 'light-hover light-bg' : 'light-hover')"
    >
        <v-icon class="mr-2" :color="timeline.color">mdi-circle</v-icon>
        {{ timeline.name }}
        <v-tooltip top>
          <template v-slot:activator="{ on }">
            <v-btn
              v-show="!isMultiAnalyzer"
              text
              x-small
              icon
              v-on="on"
              class="ml-1"
              :ripple="false"
            >
              <v-icon small color="#696B69">mdi-information-outline</v-icon>
            </v-btn>
          </template>
          <span>Severity: Note</span>
        </v-tooltip>
      </div>

    <v-expand-transition>
      <div
        v-if="!isMultiAnalyzer"
        v-show="expanded"
        :class="$vuetify.theme.dark ? (expanded ? 'dark-hover dark-bg' :'dark-hover') : (expanded ? 'light-hover light-bg' : 'light-hover')"
      >
        <v-simple-table dense class="ml-2">
          <tbody
            :class="$vuetify.theme.dark ? (expanded ? 'dark-hover dark-bg' :'dark-hover') : (expanded ? 'light-hover light-bg' : 'light-hover')"
          >
            <tr class="pr-3">
              <td width="80" style="border: none">
                <strong>Verdict:</strong>
              </td>
              <td style="border: none">
                <span>
                  {{ timeline.result }}
                </span>
              </td>
            </tr>
            <tr>
              <td style="border: none">
                <strong>Last run:</strong>
              </td>
              <td style="border: none">
                <span>
                  {{ timeline.created_at }}
                </span>
              </td>
            </tr>
            <tr>
              <td width="80" style="border: none">
                <strong>Status:</strong>
              </td>
              <td style="border: none">
                <span>
                  {{ timeline.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </v-simple-table>
      </div>
      <div v-else v-show="expanded" class="ml-3 pb-1 mr-2">
        <v-icon>mdi-alert-octagon-outline</v-icon>
        <span class="ml-1">Showing multi analyzer results is not supported in the new UI yet. Please visit the old UI to see these results.</span>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>

export default {
  props: ['timeline', 'isMultiAnalyzer'],
  data: function () {
    return {
      expanded: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  methods: {

  },
}
</script>

<style scoped lang="scss">
.dark-bg {
  background-color: #303030;
}
.light-bg {
  background-color: #F6F6F6;
}
</style>
