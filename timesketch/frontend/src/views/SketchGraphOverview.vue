<!--
Copyright 2020 Google Inc. All rights reserved.

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
        <ts-navbar-secondary currentAppContext="sketch" currentPage="graph"></ts-navbar-secondary>
      </div>
    </section>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <div class="notification is-warning">
              <span class="title is-4">Timesketch Graphs</span>
              <p>
                This is a new <strong>experimental feature</strong> for graph visualisation of timeline data.
                It consist of a server side plugin framework and an interactive frontend UI for exploring.
              </p>
            </div>
            <br><br>
            <span class="title is-6 is-uppercase">System generated</span>
            <router-link :to="{ name: 'SketchGraphExplore', query: {plugin: graphPlugin.name}}" v-for="graphPlugin in graphs" :key="graphPlugin.name">
              <ul class="content-list">
                <li style="padding:10px;border-bottom:none;cursor:pointer;">
                  <strong style="color: var(--default-font-color)">{{ graphPlugin.display_name }}</strong>
                  <br>
                  <span>{{ graphPlugin.description }}</span>
                </li>
              </ul>
            </router-link>
            <br><br>
            <span class="title is-6 is-uppercase">Saved by users</span>
                <router-link :to="{ name: 'SketchGraphExplore', query: {graph: savedGraph.id}}" v-for="savedGraph in savedGraphs" :key="savedGraph.id">
                  <ul class="content-list">
                  <li style="padding:10px;border-bottom:none;cursor:pointer;">
                    <strong style="color: var(--default-font-color)">{{ savedGraph.name }}</strong>
                    <br>
                    <span>Created: {{ savedGraph.created_at | moment("YYYY-MM-DD HH:mm") }}</span>
                  </li>
                  </ul>
                </router-link>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import ApiClient from "../utils/RestApiClient"

export default {
  props: ['sketchId'],
  computed: {
    sketch () {
      return this.$store.state.sketch
    }
  },
  data() {
    return {
      graphs: {},
      savedGraphs: [],
    }
  },
  created() {
    ApiClient.getGraphPluginList().then((response) => {
        this.graphs = response.data
      }).catch((e) => {
        console.error(e)
    })
    ApiClient.getSavedGraphList(this.sketch.id).then((response) => {
      let graphs = response.data['objects'][0]
      if (graphs !== undefined) {
        this.savedGraphs = response.data['objects'][0]
      }
      }).catch((e) => {
        console.error(e)
    })

  }
}
</script>
