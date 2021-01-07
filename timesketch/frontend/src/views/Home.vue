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
        <input v-on:keyup.enter="search" v-model="searchQuery" class="ts-home-input" type="text" placeholder="Search for investigations" autofocus>
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

    <section class="section" v-if="newSearchQuery">
      <div class="container">
        <div class="card">
          <header class="card-header">
            <div class="card-header-title">
              Search results
            </div>
          </header>
          <div class="card-content">
            <ts-sketch-list scope="search" :search-query="newSearchQuery"></ts-sketch-list>
            <hr>
            <button class="button is-info" v-on:click="newSearchQuery = ''">Back</button>
          </div>
        </div>
      </div>
    </section>

    <section class="section" v-if="!newSearchQuery">
      <div class="container">
        <div class="card">
          <header class="card-header">
            <div class="card-header-title">
              My recent activity
            </div>
          </header>
          <div class="card-content">
            <ts-sketch-list scope="recent"></ts-sketch-list>
          </div>
        </div>
      </div>
      <br>
    </section>

    <section class="section" v-if="!newSearchQuery">
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

    <section class="section" v-if="!newSearchQuery">
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

    <section class="section" v-if="!newSearchQuery">
      <div class="container">
        <div class="card">
          <header class="card-header">
            <div class="card-header-title">
              Archived
            </div>
          </header>
          <div class="card-content">
            <ts-sketch-list scope="archived"></ts-sketch-list>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
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
      searchQuery: '',
      newSearchQuery: ''
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
    },
    search: function () {
      this.newSearchQuery = this.searchQuery
    }
  },
  created: function () {
    this.$store.dispatch('resetState')
    document.title = 'Timesketch'
  }
}
</script>
