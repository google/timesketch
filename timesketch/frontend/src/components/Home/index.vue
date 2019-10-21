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

    <!-- Secondary navigation -->
    <section class="section">
      <div class="container">
        <ts-navbar-secondary>
          <button v-if="sketches" class="button is-success is-rounded" v-on:click="showSketchCreateModal = !showSketchCreateModal"><strong>+ Sketch</strong></button>
        </ts-navbar-secondary>
      </div>
    </section>

    <div class="modal" v-bind:class="{ 'is-active': showSketchCreateModal }">>
      <div class="modal-background"></div>
      <div class="modal-content">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Create new sketch</p>
          </header>
          <div class="card-content">
            <div class="content">
              <ts-create-sketch-form></ts-create-sketch-form>
            </div>
          </div>
        </div>
      </div>
      <button class="modal-close is-large" aria-label="close" v-on:click="showSketchCreateModal = !showSketchCreateModal"></button>
    </div>

    <div class="section">
      <div class="container">
        <div class="card">
          <div class="card-content">
            <div v-if="!sketches" class="has-text-centered">
              <h1 class="title">Welcome to Timesketch</h1>
              <button class="button is-success is-rounded" v-on:click="showSketchCreateModal = !showSketchCreateModal"><strong>Create sketch</strong></button>
            </div>
            <ts-sketch-list :sketches="sketches"></ts-sketch-list>
          </div>
        </div>
      </div>
    </div>

  </div>

</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsSketchList from './SketchList'
import TsCreateSketchForm from './CreateSketchForm'

export default {
  name: 'ts-home',
  components: {
    TsSketchList,
    TsCreateSketchForm
  },
  data () {
    return {
      showSketchCreateModal: false,
      sketches: []
    }
  },
  created: function () {
    ApiClient.getSketchList().then((response) => {
      this.$store.commit('resetState')
      this.sketches = response.data.objects[0]
    }).catch((e) => {
      console.error(e)
    })
  }
}
</script>

<style lang="scss"></style>
