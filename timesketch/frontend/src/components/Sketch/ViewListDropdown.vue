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
    <div class="dropdown" v-bind:class="{'is-active': viewListDropdownActive}">
      <div class="dropdown-trigger">
        <a class="button" v-bind:class="{'is-rounded': isRounded, 'is-small': isSmall}" aria-haspopup="true" aria-controls="dropdown-menu" v-on:click="viewListDropdownActive = !viewListDropdownActive">
          <span>{{ title || 'Saved searches' }}</span>
          <span class="icon is-small">
            <i class="fas fa-angle-down" aria-hidden="true"></i>
          </span>
        </a>
      </div>
      <div class="dropdown-menu" id="dropdown-menu" role="menu">
        <div class="dropdown-content">
          <span class="dropdown-item" v-if="meta.views && meta.views.length < 1">No saved searches</span>
          <span class="dropdown-item" v-if="title">
            <button class="button is-small is-rounded is-fullwidth" @click="clearSearch">Clear</button>
          </span>
          <a class="dropdown-item" v-on:click="setActiveView(view)" v-for="view in meta.views" :key="view.id">
            <span>{{ view.name }}</span>
          </a>
        </div>
      </div>
    </div>

    <a v-if="queryHasChanged" v-on:click="$emit('updateView', activeView)" class="button is-small is-warning" style="margin-left:10px;">
      <span>Update saved search</span>
    </a>

  </div>
</template>

<script>
import EventBus from "../../main"

export default {
  props: ['currentQueryString', 'currentQueryFilter', 'isRounded', 'isSmall'],
  data () {
    return {
      viewListDropdownActive: false,
      activeView: null,
      queryHasChanged: false,
      title: '',
    }
  },
  methods: {
    setActiveView: function (view) {
      this.$emit('setActiveView', view)
      this.title = view.name
      this.viewListDropdownActive = false
      this.activeView = view
      this.queryHasChanged = false
    },
    clearSearch: function (view) {
      this.$emit('clearSearch')
      this.title = ''
      this.viewListDropdownActive = false
      this.activeView = null
      this.queryHasChanged = false
    },
    foobar: function () {

      if (!this.activeView) {
        return
      }

      if (this.currentQueryString === '') {
        return
      }

      let queryMatch = this.currentQueryString === this.activeView.query
      let filterMatch = JSON.stringify(this.currentQueryFilter) === JSON.stringify(JSON.parse(this.activeView.filter))
      console.log('Change: ', !filterMatch || !queryMatch)
      this.queryHasChanged = !queryMatch || !filterMatch
    }
  },
  computed: {
    meta () {
      return this.$store.state.meta
    }
  },
  created: function () {
    EventBus.$on('newSearch', this.foobar)
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
<style scoped lang="scss"></style>
