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
    <router-link
      :to="{ name: 'GraphExplore', query: { plugin: graph.name } }"
      v-for="graph in graphs"
      :key="graph.name"
    >
      <ul class="content-list">
        <li style="padding:10px;border-bottom:none;cursor:pointer;">
          <strong style="color: var(--default-font-color)">{{ graph.display_name }}</strong>
          <br />
          <span>{{ graph.description }}</span>
        </li>
      </ul>
    </router-link>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  data() {
    return {
      graphs: [],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  created() {
    ApiClient.getGraphPluginList()
      .then(response => {
        this.graphs = response.data
      })
      .catch(e => {
        console.error(e)
      })
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
