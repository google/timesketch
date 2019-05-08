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

    <section class="section">
      <div class="container">
        <ts-navbar-secondary currentAppContext="sketch" currentPage="stories">
          <a class="button is-success is-rounded" style="margin-right:7px;" v-on:click="showCreateStoryModal = !showCreateStoryModal">
              <span class="icon is-small">
                <i class="fas fa-plus"></i>
              </span>
            <span>Story</span>
          </a>
        </ts-navbar-secondary>
      </div>
    </section>

    <div class="modal" v-bind:class="{ 'is-active': showCreateStoryModal }">>
      <div class="modal-background"></div>
      <div class="modal-content">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Create a new story</p>
          </header>
          <div class="card-content">
            <div class="content">
              <ts-sketch-story-create-form @toggleModal="showCreateStoryModal = !showCreateStoryModal"></ts-sketch-story-create-form>
            </div>
          </div>
        </div>
      </div>
      <button class="modal-close is-large" aria-label="close" v-on:click="showCreateStoryModal = !showCreateStoryModal"></button>
    </div>

    <section class="section">
      <div class="container">
        <div class="card">
          <div class="card-content">
            <ts-sketch-story-list></ts-sketch-story-list>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import TsSketchStoryList from './SketchStoryList'
import TsSketchStoryCreateForm from './SketchStoryCreateForm'

export default {
  name: 'ts-sketch-story',
  components: {
    TsSketchStoryList,
    TsSketchStoryCreateForm
  },
  data () {
    return {
      showCreateStoryModal: false
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

<style lang="scss"></style>
