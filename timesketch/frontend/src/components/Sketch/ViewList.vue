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
    <ul class="content-list">
      <li style="padding:10px;border-bottom:none;" v-for="(view, index) in views" :key="view.id">
        <router-link :to="{ name: 'SketchExplore', query: {view: view.id}}"><strong>{{ view.name }}</strong></router-link>
        <br>
        <span v-if="!controls" class="is-size-7">
          Created {{ view.created_at | moment("YYYY-MM-DD HH:mm") }} <span v-if="view.user"> by {{ view.user }}</span> <span v-if="view.description"> ({{ view.description }})</span>
        </span>
        <span v-if="controls" class="is-size-7">
          <b>Query:</b> {{ view.query }}
        </span>
        <div v-if="controls" class="field is-grouped is-pulled-right" style="margin-top: -15px;">
          <p class="control">
            <button v-on:click="remove(view, index)" class="button is-small is-rounded is-danger is-outlined">Remove</button>
          </p>
        </div>
      </li>
    </ul>
  </div>
</template>

<script>
import Vue from 'vue'
import ApiClient from '../../utils/RestApiClient'

export default {
  props: ['views', 'controls'],
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    }
  },
  methods: {
    remove (view, index) {
      Vue.delete(this.views, index)
      ApiClient.deleteView(this.sketch.id, view.id).then((response) => {
      }).catch((e) => {
        console.error(e)
      })
    }
  }

}
</script>
