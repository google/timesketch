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

    <ts-navbar-main>
      <template v-slot:center>
        <input v-model="search" class="ts-home-input" type="text" placeholder="Search for investigations" autofocus>
      </template>
    </ts-navbar-main>

    <!-- Secondary navigation -->
    <section class="section" style="margin-top:20px; margin-bottom: 20px;">
      <div class="container">
          <button class="button is-success" v-on:click="showSketchCreateModal = !showSketchCreateModal">
            <span class="icon is-small">
              <i class="fas fa-plus-circle"></i>
            </span>
            <strong>New investigation</strong>
          </button>
      </div>
    </section>

    <b-modal :active.sync="showSketchCreateModal" :width="640" scroll="keep">
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
    </b-modal>

    <!--
    <div v-if="!loading && !mySketches.length && !sharedSketches.length" class="has-text-centered">
      <h1 class="title">Welcome to Timesketch</h1>
      <button class="button is-success is-rounded" v-on:click="showSketchCreateModal = !showSketchCreateModal"><strong>Create sketch</strong></button>
    </div>
    -->

    <div v-if="search" class="section">
      <div class="container">
        <div class="card">
          <div class="card-content">
            <p v-if="!filteredList.length">No search results</p>
            <ts-sketch-list v-if="filteredList.length" :sketches="filteredList"></ts-sketch-list>
          </div>
        </div>
      </div>
    </div>

    <section class="section">
      <div class="container">
        <div class="card">
          <header class="card-header">
            <div class="card-header-title">
              My investigations
            </div>
          </header>
          <div class="card-content">
            <ts-sketch-list scope="user"></ts-sketch-list>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="card">
          <header class="card-header">
            <div class="card-header-title">
              Shared with me
            </div>
          </header>
          <div class="card-content">
            <ts-sketch-list scope="shared"></ts-sketch-list>
          </div>
        </div>
      </div>
    </section>

    <!--
    <div v-if="allSketches.length && !search" class="section">
      <div class="container">
        <div class="card">
          <div class="card-content">
            <b-tabs v-model="activeTab">
                <b-tab-item label="My sketches" :disabled="!mySketches.length">
                  <div class="card">
                    <div class="card-content">
                      <ts-sketch-list :sketches="mySketches"></ts-sketch-list>
                    </div>
                  </div>
                </b-tab-item>

                <b-tab-item label="Shared with me" :disabled="!sharedSketches.length">
                  <div class="card">
                    <div class="card-content">
                      <ts-sketch-list :sketches="sharedSketches"></ts-sketch-list>
                    </div>
                  </div>
                </b-tab-item>

                <b-tab-item label="Archived" :disabled="!myArchivedSketches.length">
                  <div class="card">
                    <div class="card-content">
                      <ts-sketch-list :sketches="myArchivedSketches"></ts-sketch-list>
                    </div>
                  </div>
                </b-tab-item>
            </b-tabs>
          </div>
        </div>
      </div>
    </div>
    -->

  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsSketchList from '../components/Home/SketchList'
import TsCreateSketchForm from '../components/Home/CreateSketchForm'
import TsNavbarMain from "../components/AppNavbarMain"

export default {
  components: {
    TsNavbarMain,
    TsSketchList,
    TsCreateSketchForm
  },
  data () {
    return {
      showSketchCreateModal: false,
      allSketches: [],
      mySketches: [],
      myArchivedSketches: [],
      sharedSketches: [],
      loading: true,
      isFullPage: true,
      loadingComponent: null,
      search: ''
    }
  },
  computed: {
    filteredList() {
      return this.allSketches.filter(sketch => {
        return sketch.name.toLowerCase().includes(this.search.toLowerCase())
      })
    }
  },
  methods: {
    loadingOpen: function () {
      this.loading = true
      this.loadingComponent = this.$buefy.loading.open({
        container: this.isFullPage ? null : this.$refs.element.$el
      })
    },
    loadingClose: function () {
      this.loading = false
      this.loadingComponent.close()
    }
  },
  created: function () {
    //this.loadingOpen()
    this.$store.dispatch('resetState')
    document.title = 'Timesketch'
  }
}
</script>
