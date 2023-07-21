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
    <h3>Rename sketch</h3>
    <br />
    <v-form @submit.prevent="renameSketch()">
      <v-text-field outlined dense autofocus v-model="newSketchName" @focus="$event.target.select()"> </v-text-field>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="closeDialog()"> Cancel </v-btn>
        <v-btn text color="primary" @click="renameSketch()"> Save </v-btn>
      </v-card-actions>
    </v-form>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

export default {
  data() {
    return {
      newSketchName: '',
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  methods: {
    renameSketch() {
      ApiClient.saveSketchSummary(this.sketch.id, this.newSketchName, '')
        .then((response) => {
          this.$store.dispatch('updateSketch', this.sketch.id).then(() => {})
        })
        .catch((e) => {
          console.error(e)
        })
      this.$emit('close')
    },
    closeDialog: function () {
      this.newSketchName = this.sketch.name
      this.$emit('close')
    },
  },
  created() {
    this.newSketchName = this.sketch.name
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
