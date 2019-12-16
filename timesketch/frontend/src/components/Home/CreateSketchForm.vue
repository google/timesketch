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
      <label class="label">Name</label>
      <div class="control">
        <input v-model="form.name" class="input" type="text" required placeholder="Name your sketch" autofocus>
      </div>
    </div>
    <div class="field">
      <label class="label">Description (optional)</label>
      <div class="control">
        <textarea v-model="form.description" class="textarea" placeholder="Describe your sketch"></textarea>
      </div>
    </div>
    <div class="field">
      <div class="control">
        <input class="button is-success" type="submit" value="Save">
      </div>
    </div>
  </form>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  data () {
    return {
      form: {
        name: '',
        description: ''
      }
    }
  },
  methods: {
    clearFormData: function () {
      this.form.name = ''
      this.form.description = ''
    },
    submitForm: function () {
      let formData = {
        name: this.form.name,
        description: this.form.description
      }
      ApiClient.createSketch(formData).then((response) => {
        let newSketchId = response.data.objects[0].id
        this.clearFormData()
        this.$router.push({ name: 'SketchOverview', params: { sketchId: newSketchId } })
      }).catch((e) => {})
    }
  }
}
</script>

