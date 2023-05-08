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
  <span>
    <span v-for="tag in sortedTags" :key="tag">
      <v-hover v-slot="{ hover }">
        <v-chip
          :style="hover ? '' : 'padding-right: 32px'"
          small
          class="mr-1"
          :close="hover ? true : false"
          @click:close="removeTag(item, tag)"
          :color="tagColor(tag).color"
          :text-color="tagColor(tag).textColor"
        >
          <v-icon v-if="tag in tagConfig" left small>{{ tagConfig[tag].label }}</v-icon>
          {{ tag }}
        </v-chip>
      </v-hover>
    </span>
    <span v-for="label in item._source.label" :key="label">
      <v-chip v-if="!label.startsWith('__ts')" small outlined class="mr-2">
        {{ label }}
      </v-chip>
    </span>
  </span>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
export default {
  props: ['item', 'tagConfig', 'showDetails'],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    sortedTags() {
      if (!this.item._source.tag) return []
      // place quickTags first in the array, sort the rest alphabetically
      let tags = this.item._source.tag
      tags.sort((a, b) => {
        // TODO: refactor when quickTags become configurable.
        if (a === 'bad') {
          return -1
        }
        if (b === 'bad') {
          return 1
        }
        if (a === 'suspicious') {
          return -1
        }
        if (b === 'suspicious') {
          return 1
        }
        if (a === 'good') {
          return -1
        }
        if (b === 'good') {
          return 1
        }
        return a.localeCompare(b)
      })
      return tags
    },
  },
  methods: {
    tagColor: function (tag) {
      if (this.tagConfig[tag]) {
        return this.tagConfig[tag]
      }
      return 'lightgrey'
    },
    removeTag(item, tag) {
      ApiClient.untagEvents(this.sketch.id, [item], [tag])
        .then((response) => {
          item._source.tag.splice(item._source.tag.indexOf(tag), 1)
          this.$store.dispatch('updateTimelineTags', { sketchId: this.sketch.id, tag: tag, num: -1 })
        })
        .catch((e) => {
          console.error(e)
        })
    },
  },
}
</script>
