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
  <v-menu v-model="showMenu" offset-x :close-on-content-click="false">
    <template v-slot:activator="{ on, attrs }">
      <v-icon title="Modify tags" v-if="assignedTags.length > 0" v-bind="attrs" v-on="on" class="ml-1">mdi-tag-plus</v-icon>
      <v-icon title="Modify tags" v-else v-bind="attrs" v-on="on" class="ml-1">mdi-tag-plus-outline</v-icon>
    </template>

    <ts-event-tag-dialog :events="[event]" @close="showMenu = false"></ts-event-tag-dialog>

  </v-menu>
</template>

<script>
import TsEventTagDialog from './EventTagDialog.vue'

export default {
  components: {
    TsEventTagDialog
  },
  props: ['event'],
  data() {
    return {
      showMenu: false,
      selectedTags: null,
      // TODO: Refactor this into a configurable option
      quickTags: [
        { tag: 'bad', color: 'red', textColor: 'white', label: 'mdi-alert-circle-outline' },
        { tag: 'suspicious', color: 'orange', textColor: 'white', label: 'mdi-help-circle-outline' },
        { tag: 'good', color: 'green', textColor: 'white', label: 'mdi-check-circle-outline' },
      ],
      search: null,
    }
  },
  computed: {
    assignedTags() {
      if (!this.event._source.tag) return []
      return this.event._source.tag
    },
  },
}
</script>

<style scoped lang="scss"></style>
