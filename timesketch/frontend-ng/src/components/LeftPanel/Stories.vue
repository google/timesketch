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
  <div>
    <div
      no-gutters
      :style="!(meta.stories && meta.stories.length) ? '' : 'cursor: pointer'"
      class="pa-4"
      flat
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> <v-icon left>mdi-book-open-outline</v-icon> Stories </span>
      <v-btn
        icon
        v-if="expanded || !meta.stories.length"
        text
        class="float-right mt-n1 mr-n1"
        @click="createStory()"
        @click.stop=""
      >
        <v-icon>mdi-plus</v-icon>
      </v-btn>

      <span v-if="!expanded" class="float-right" style="margin-right: 10px">
        <small v-if="meta.stories.length"
          ><strong>{{ meta.stories.length }}</strong></small
        >
      </span>
    </div>

    <v-expand-transition>
      <div v-show="expanded && meta.stories.length">
        <router-link
          v-for="story in meta.stories"
          :key="story.id"
          :to="{ name: 'Story', params: { storyId: story.id } }"
          style="cursor: pointer; font-size: 0.9em; text-decoration: none"
        >
          <v-row no-gutters class="pa-2 pl-5" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
            <span :class="$vuetify.theme.dark ? 'dark-font' : 'light-font'">{{ story.title }}</span>
          </v-row>
        </router-link>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

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
  },
  methods: {
    createStory() {
      let title = 'Untitled story'
      let content = ''
      ApiClient.createStory(title, content, this.sketch.id)
        .then((response) => {
          let newStoryId = response.data.objects[0].id
          this.$router.push({ name: 'Story', params: { storyId: newStoryId } })
          this.$store.dispatch('updateSketch', this.sketch.id)
        })
        .catch((e) => {})
    },
  },
}
</script>
