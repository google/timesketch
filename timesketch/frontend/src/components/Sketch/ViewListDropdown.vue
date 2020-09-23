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
</template>

<script>
export default {
  props: ['isRounded', 'isSmall'],
  data () {
    return {
      viewListDropdownActive: false,
      title: '',
    }
  },
  methods: {
    setActiveView: function (view) {
      this.$emit('setActiveView', view)
      this.title = view.name
      this.viewListDropdownActive = false
    },
    clearSearch: function () {
      this.$emit('clearSearch')
      this.title = ''
      this.viewListDropdownActive = false
    }
  },
  computed: {
    meta () {
      return this.$store.state.meta
    }
  },
  created: function () {
    let viewId = this.$route.query.view
    let view =  this.meta.views.filter(function(view) {
      return view.id === parseInt(viewId);
    });
    this.setActiveView(view[0])
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
