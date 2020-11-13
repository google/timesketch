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
                <ts-create-view-form @setActiveView="setActiveView($event)" :sketchId="sketchId" :currentQueryString="currentQueryString" :currentQueryFilter="currentQueryFilter"></ts-create-view-form>
              </div>
            </div>
          </div>
        </b-modal>

        <b-dropdown ref="dropdown" animation="none" aria-role="menu" append-to-body>

          <a class="button" v-bind:class="{ 'is-rounded': isSimple, 'ts-search-dropdown': !isSimple}" slot="trigger" slot-scope="{ active }">
            <b-icon v-if="!isSimple" icon="save" style="margin-right: 7px; font-size: 0.6em;"></b-icon>
            <span v-if="activeView" style="margin-right: 7px;">{{ isSimple ? '+ Saved search' : activeView.name }}</span>
            <span v-if="isSimple">+ Saved search</span>
            <b-icon :icon="active ? 'chevron-up' : 'chevron-down'" style="font-size: 0.6em;"></b-icon>
          </a>

          <div class="modal-card" style="width:500px;color: var(--font-color-dark);">
            <section class="modal-card-body">
              <div v-if="!isSimple">
                <p>
                  Save search query and filters that you want to use again.
                </p>
                <hr>
              </div>
              <div v-if="meta.views.length">
                <b-dropdown-item v-on:click="setActiveView(view)" v-for="view in meta.views" :key="view.id">
                  <span>{{ view.name }}</span>
                </b-dropdown-item>
              </div>
              </section>
          </div>

          <div class="level footer" v-if="!isSimple">
            <div class="level-left">
              <div class="level-item">
                <button class="button is-text" style="color: var(--font-color-dark); text-decoration: none;" @click="clearSearch" v-if="activeView">Clear</button>
              </div>
            </div>
            <div class="level-right">
              <div class="level-item">
                <button class="button level-item" style="border-radius: 5px;" @click="updateView" v-if="activeView" :disabled="!currentQueryString">Save changes</button>
              </div>
              <div class="level-item">
                <button class="button is-info level-item" style="border-radius: 5px;" :disabled="!currentQueryString" @click="saveView">
                  <b-icon icon="save" size="is-small"></b-icon>
                  <span>{{ activeView ? 'Save as new': 'Save current search' }}</span>
                </button>
              </div>
            </div>
          </div>

        </b-dropdown>

  </div>
</template>

<script>
import ApiClient from "../../utils/RestApiClient"
import TsCreateViewForm from './CreateViewForm'

export default {
  components: {
    TsCreateViewForm
  },
  props: ['currentQueryString', 'currentQueryFilter', 'isSimple', 'sketchId'],
  data () {
    return {
      activeView: null,
      showCreateViewModal: false
    }
  },
  methods: {
    setActiveView: function (view, doSearch=true) {
      this.showCreateViewModal = false
      this.activeView = view
      if (doSearch) {
        this.$emit('setActiveView', view)
      }

    },
    clearSearch: function () {
      this.$emit('clearSearch')
      this.activeView = null
      this.$refs.dropdown.toggle()
    },
    saveView: function () {
      this.showCreateViewModal = true
      this.$refs.dropdown.toggle()
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
    }
  },
  computed: {
    meta () {
      return this.$store.state.meta
    }
  },
  created: function () {
    let queryViewId = this.$route.query.view
    if (queryViewId) {
      let view =  this.meta.views.filter(function(view) {
        return view.id === parseInt(queryViewId);
      })
      this.setActiveView(view[0], false)
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.button:focus, .button.is-focused {
  border-color: transparent;
}

.footer {
  background: #f5f5f5;
  border-top: solid 1px #d1d1d1;
  padding: 15px;
}

</style>
