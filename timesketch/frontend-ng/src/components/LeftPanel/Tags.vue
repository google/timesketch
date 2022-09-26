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
  <div v-if="tags.length">
    <div
      style="cursor: pointer"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
      class="pa-2"
    >
      <span>
        <v-icon v-if="!expanded">mdi-chevron-right</v-icon>
        <v-icon v-else>mdi-chevron-down</v-icon>
      </span>

      <span style="font-size: 0.9em">Tags ({{ tags.length }})</span>
    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <v-divider></v-divider>
        <v-simple-table dense>
          <template v-slot:default>
            <tbody>
              <tr v-for="tag in tags" :key="tag.tag">
                <td @click="search(tag.tag)">
                  <a>{{ tag.tag }}</a>
                </td>
                <td>{{ tag.count | compactNumber }}</td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import EventBus from '../../main'

const defaultQueryFilter = () => {
  return {
    from: 0,
    terminate_after: 40,
    size: 40,
    indices: '_all',
    order: 'asc',
    chips: [],
  }
}

export default {
  props: [],
  data: function () {
    return {
      expanded: false,
    }
  },
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
  methods: {
    search(tag) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = 'tag:' + '"' + tag + '"'
      eventData.queryFilter = defaultQueryFilter()
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
}
</script>
