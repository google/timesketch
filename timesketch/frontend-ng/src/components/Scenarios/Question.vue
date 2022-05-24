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
  <div>
    <div :class="highlightColor">
      <div class="pa-2 pl-4" @click="expanded = !expanded" style="cursor: pointer">
        <v-menu open-on-hover offset-y :open-delay="1000" :close-on-content-click="false">
          <template v-slot:activator="{ on, attrs }">
            <span style="font-size: 0.9em" v-bind="attrs" v-on="on">{{ question.display_name }}</span>
          </template>
          <v-card style="font-size: 0.9em" class="pa-3" width="400">
            {{ question.description }}
          </v-card>
        </v-menu>
      </div>

      <div v-show="expanded">
        <div style="font-size: 0.9em" class="pa-4">
          <v-textarea disabled outlined flat hide-details auto-grow rows="3">
            <template v-slot:prepend-inner>
              <v-avatar color="grey" class="mt-n1" size="28"></v-avatar>
            </template>
          </v-textarea>
          <v-card-actions class="pl-0">
            <v-btn disabled x-small outlined color="primary"> Answer Yes </v-btn>
            <v-btn disabled x-small outlined color="primary"> Answer No </v-btn>
            <v-btn disabled x-small outlined color="primary"> Inconclusive </v-btn>
          </v-card-actions>
        </div>
      </div>

      <v-divider></v-divider>
    </div>
  </div>
</template>

<script>
export default {
  props: ['question'],
  data: function () {
    return {
      expanded: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    highlightColor() {
      if (!this.expanded) {
        return
      }
      return this.$vuetify.theme.dark ? 'dark-highlight' : 'light-highlight'
    },
  },
  methods: {},
  created() {},
}
</script>

<style scoped lang="scss">
.selected {
  font-weight: bold;
  background-color: #f5f5f5;
}
</style>
