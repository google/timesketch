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

        <b-modal :active.sync="showCreateViewModal" :width="640" scroll="keep">
          <div class="card">
            <header class="card-header">
              <p class="card-header-title">Save search</p>
            </header>
            <div class="card-content">
              <div class="content">
                <ts-create-view-form @toggleCreateViewModal="showCreateViewModal = !showCreateViewModal" :sketchId="sketchId" :currentQueryString="currentQueryString" :currentQueryFilter="currentQueryFilter"></ts-create-view-form>
              </div>
            </div>
          </div>
        </b-modal>

        {{activeView}}

        <b-dropdown ref="dropdown" aria-role="menu">

          <a class="button ts-search-dropdown" slot="trigger" slot-scope="{ active }">
            <b-icon icon="save" style="margin-right: 7px; font-size: 0.6em;"></b-icon>
            <span v-if="activeView" style="margin-right: 7px;">{{ activeView.name }}</span>
            <b-icon :icon="active ? 'chevron-up' : 'chevron-down'" style="font-size: 0.6em;"></b-icon>
          </a>

          <div class="modal-card" style="width:500px;color: var(--font-color-dark);">
            <section class="modal-card-body">
              <p>
                Save search query and filters that you want to use again.
              </p>
              <hr>
              <div v-if="meta.views.length">
                <b>Saved searches</b>
                <b-dropdown-item v-on:click="setActiveView(view)" v-for="view in meta.views" :key="view.id">
                  <span>{{ view.name }}</span>
                </b-dropdown-item>
              </div>
              </section>
            </div>

          <footer class="modal-card-foot">
            <button class="button" style="border-radius: 5px;" @click="clearSearch" v-if="activeView">Clear</button>
            <button class="button" style="border-radius: 5px;" @click="updateView" v-if="activeView">Save changes</button>
            <button class="button is-info" style="border-radius: 5px;" @click="showCreateViewModal = !showCreateViewModal" v-if="activeView">Save as new</button>
            <button class="button is-info" style="border-radius: 5px;" @click="showCreateViewModal = !showCreateViewModal" v-if="!activeView">Save search</button>
          </footer>

        </b-dropdown>

  </div>
</template>

<script>
import EventBus from "../../main"
import ApiClient from "../../utils/RestApiClient"
import TsCreateViewForm from './CreateViewForm'

export default {
  components: {
    TsCreateViewForm
  },
  props: ['currentQueryString', 'currentQueryFilter', 'isRounded', 'isSmall', 'sketchId'],
  data () {
    return {
      activeView: null,
      title: '',
      showCreateViewModal: false
    }
  },
  methods: {
    setActiveView: function (view) {
      this.$emit('setActiveView', view)
      this.title = view.name
      this.activeView = view
      this.$emit('updateView', {'view': this.activeView, 'edited': false})
    },
    clearSearch: function (view) {
      this.$emit('clearSearch')
      this.title = ''
      this.activeView = null
      this.$refs.dropdown.toggle()
      this.$emit('updateView', {'view': null, 'edited': false})

    },
    updateView: function () {
      if (!this.activeView) {
        return
      }
      this.$refs.dropdown.toggle()
      this.activeView.query = this.currentQueryString
      this.activeView.filter = JSON.stringify(this.currentQueryFilter)
      ApiClient.updateView(this.sketchId, this.activeView.id, this.currentQueryString, this.currentQueryFilter)
       .then((response) => {
         this.$buefy.toast.open('Saved search has been updated')
       })
       .catch((e) => {})
    },
    compareView: function () {
      if (!this.activeView) {
        return
      }
      let queryMatch = this.currentQueryString === this.activeView.query
      let filterMatch = JSON.stringify(this.currentQueryFilter) === JSON.stringify(JSON.parse(this.activeView.filter))
      if (!queryMatch || !filterMatch) {
        this.$emit('updateView', {'view': this.activeView, 'edited': true})
      } else {
        this.$emit('updateView', {'view': this.activeView, 'edited': false})
      }
    }
  },
  computed: {
    meta () {
      return this.$store.state.meta
    }
  },
  created: function () {
    EventBus.$on('newSearch', this.compareView)
    let queryViewId = this.$route.query.view
    if (queryViewId) {
      let view =  this.meta.views.filter(function(view) {
        return view.id === parseInt(queryViewId);
      })
      this.setActiveView(view[0])
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.button:focus, .button.is-focused {
  border-color: transparent;
}
</style>
