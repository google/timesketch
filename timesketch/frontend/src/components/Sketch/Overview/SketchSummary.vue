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
  <div>
    <h4 class="title is-4" :contenteditable="meta.permissions.write" v-text="sketch.name" @blur="onEditTitle" @keydown.enter.prevent="onEditTitle"></h4>
    <p :contenteditable="meta.permissions.write" v-text="sketch.description" @blur="onEditDescription" @keydown.enter.prevent="onEditDescription"></p>
  </div>
</template>

<script>
import ApiClient from '../../../utils/RestApiClient'

export default {
  name: 'ts-sketch-summary',
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    }
  },
  methods: {
    onEditTitle (e) {
      this.sketch.name = e.target.innerText
      this.saveSketchSummary()
    },
    onEditDescription (e) {
      this.sketch.description = e.target.innerText
      this.saveSketchSummary()
    },
    saveSketchSummary () {
      ApiClient.saveSketchSummary(this.sketch.id, this.sketch.name, this.sketch.description).then((response) => {}).catch((e) => {
        console.error(e)
      })
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
