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
  <form v-on:submit.prevent="submitForm">
    <div class="field">
      <div class="file has-name">
        <label class="file-label">
          <input class="file-input" type="file" name="resume" v-on:change="setFileName($event.target.files)">
          <span class="file-cta">
            <span class="file-icon">
              <i class="fas fa-upload"></i>
            </span>
            <span class="file-label">
              Choose a file…
            </span>
          </span>
          <span class="file-name" v-if="fileName">
            <span v-if="!fileName">No file selected</span>
            {{ fileName }}
          </span>
        </label>
      </div>
    </div>

    <div class="field" v-if="fileName">
      <label class="label">Name</label>
      <div class="control">
        <input v-model="form.name" class="input" type="text" required placeholder="Name your timeline (optional)">
      </div>
    </div>

    <div class="field" v-if="fileName && percentCompleted === 0">
      <div class="control">
        <input class="button is-success" type="submit" value="Upload">
      </div>
    </div>
  </form>
    <br>
    <b-progress v-if="percentCompleted !== 0 && percentCompleted !== 100" :value="percentCompleted" show-value format="percent" type="is-info" size="is-medium"></b-progress>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  data () {
    return {
      form: {
        name: '',
        file: ''
      },
      fileName: '',
      percentCompleted: 0
    }
  },
  methods: {
    clearFormData: function () {
      this.form.name = ''
      this.form.file = ''
      this.fileName = ''
    },
    submitForm: function () {
      let formData = new FormData()
      formData.append('file', this.form.file)
      formData.append('name', this.form.name)
      formData.append('sketch_id', this.$store.state.sketch.id)
      let config = {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: function(progressEvent) {
          this.percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }.bind(this)
      }
      ApiClient.uploadTimeline(formData, config).then((response) => {
        this.$store.dispatch('updateSketch', this.$store.state.sketch.id)
        this.$emit('toggleModal')
        this.clearFormData()
        this.percentCompleted = 0
      }).catch((e) => {})
    },
    setFileName: function (fileList) {
      let fileName = fileList[0].name
      this.form.file = fileList[0]
      this.form.name = fileName.split('.').slice(0, -1).join('.')
      this.fileName = fileName
    }
  }
}
</script>
