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

    <ts-navbar-main>
      <template v-slot:left>
        {{ sketch.name }}
      </template>
    </ts-navbar-main>

    <section class="section">
      <div class="container is-fluid">
        <ts-navbar-secondary currentAppContext="sketch" currentPage="graph"></ts-navbar-secondary>
      </div>
    </section>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <div v-if="sketch.graphs.length">
              <span class="title is-6 is-uppercase">Saved graphs</span>
              <ts-graph-list></ts-graph-list>
              <br><br>
            </div>
            <span class="title is-6 is-uppercase">Graph plugins</span>
            <ts-graph-plugin-list></ts-graph-plugin-list>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import TsGraphList from "../components/Sketch/GraphList"
import TsGraphPluginList from "../components/Sketch/GraphPluginList"


export default {
  props: ['sketchId'],
  components: {TsGraphList, TsGraphPluginList},
  computed: {
    sketch () {
      return this.$store.state.sketch
    }
  }
}
</script>
