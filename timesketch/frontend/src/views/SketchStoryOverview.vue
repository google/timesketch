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
      <div class="container is-fluid">
        <ts-navbar-secondary currentAppContext="sketch" currentPage="stories">
          <a v-if="sketch.stories.length" class="button is-success is-rounded" style="margin-right:7px;" v-on:click="showCreateStoryModal = !showCreateStoryModal">
              <span class="icon is-small">
                <i class="fas fa-plus"></i>
              </span>
            <span>Story</span>
          </a>
        </ts-navbar-secondary>
      </div>
    </section>

    <b-modal :active.sync="showCreateStoryModal" :width="640" scroll="keep">
      <div class="card">
        <header class="card-header">
          <p class="card-header-title">Create a new story</p>
        </header>
        <div class="card-content">
          <div class="content">
            <ts-story-create-form @toggleModal="showCreateStoryModal = !showCreateStoryModal"></ts-story-create-form>
          </div>
        </div>
      </div>
    </b-modal>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <div v-if="!sketch.stories.length">
              There are no stories in this sketch yet.
              <br><br>
              <a class="button is-success is-rounded" style="margin-right:7px;" v-on:click="showCreateStoryModal = !showCreateStoryModal">
                <span class="icon is-small">
                  <i class="fas fa-plus"></i>
                </span>
                <span>Create a new story</span>
              </a>
            </div>
            <ts-story-list></ts-story-list>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import TsStoryList from '../components/Sketch/StoryList'
import TsStoryCreateForm from '../components/Sketch/CreateStoryForm'

export default {
  components: {
    TsStoryList,
    TsStoryCreateForm
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
