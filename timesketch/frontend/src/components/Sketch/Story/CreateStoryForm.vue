<!--
Copyright 2019 Google Inc. All rights reserved.

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
  <form v-on:submit.prevent="submitForm">
    <div class="field">
      <label class="label">Title</label>
      <div class="control">
        <input v-model="title" class="input" type="text" required placeholder="Title of your story" autofocus>
      </div>
    </div>
    <div class="field">
      <div class="control">
        <input class="button is-success" type="submit" value="Create">
      </div>
    </div>
  </form>
</template>

<script>
import ApiClient from '../../../utils/RestApiClient'

export default {
  name: 'ts-create-story-form',
  data () {
    return {
      title: ''
    }
  },
  methods: {
    clearFormData: function () {
      this.title = ''
    },
    submitForm: function () {
      let content = ''
      ApiClient.createStory(this.title, content, this.sketch.id).then((response) => {
        let newStoryId = response.data.objects[0].id
        this.clearFormData()
        this.$store.commit('updateSketch', this.sketch.id)
        this.$router.push({ name: 'StoryContent', params: { storyId: newStoryId } })
      }).catch((e) => {})
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
