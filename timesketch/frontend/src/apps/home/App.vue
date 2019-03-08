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
  <div id="app">
    <ts-navbar-main></ts-navbar-main>

    <!-- Secondary navigation -->
    <section class="section">
      <div class="container" v-bind:class="{'is-fluid': fluid}">
        <ts-navbar-secondary>
          <button class="button is-success is-rounded" v-on:click="showModal = !showModal"><strong>+ Sketch</strong></button>
        </ts-navbar-secondary>
      </div>
    </section>

    <div class="modal" v-bind:class="{ 'is-active': showModal }">>
      <div class="modal-background"></div>
      <div class="modal-content">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Create new sketch</p>
          </header>
          <div class="card-content">
            <div class="content">
              <form v-on:submit.prevent="submitForm">
                <div class="field">
                  <label class="label">Name</label>
                  <div class="control">
                    <input v-model="form.name" class="input" type="text" required placeholder="Name your sketch">
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
                    <button class="button is-success" type="submit" v-on:click="submitForm">Save</button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
      <button class="modal-close is-large" aria-label="close" v-on:click="showModal = !showModal"></button>
    </div>

    <div class="section">
      <div class="container">
      <div class="card">
        <div class="card-content">
          <div>
            <ts-sketch-list></ts-sketch-list>
          </div>
        </div>
        </div>
      </div>
    </div>

  </div>

</template>

<script>
import TsSketchList from '../../components/HomeSketchList'
import ApiClient from '../../utils/RestApiClient'

export default {
  name: 'app',
  components: {
    TsSketchList
  },
  data: function () {
    return {
      showModal: false,
      form: {
        name: '',
        description: ''
      }
    }
  },
  methods: {
    cleanFormData: function () {
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
        this.cleanFormData()
        window.location.href = '/sketch/' + newSketchId
      }).catch((e) => {})
    }
  }
}
</script>

<style lang="scss"></style>
