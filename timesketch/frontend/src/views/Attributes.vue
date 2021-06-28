<!--
Copyright 2021 Google Inc. All rights reserved.

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

    <ts-navbar-secondary currentAppContext="sketch" currentPage="attributes"></ts-navbar-secondary>

    <section class="section">
      <div class="container is-fluid">
        <div class="card" style="min-height:160px;">
          <header class="card-header">
            <p class="card-header-title">Attribute list</p>
          </header>
          <div class="card-content">
            <b-table :data="sketchAttributes" default-sort="name">
              <b-table-column field="name" label="Attribute name" v-slot="data">
                {{ data.row.name }}
              </b-table-column>
              <b-table-column field="ontology" label="Ontology" v-slot="data">
                <code>{{ data.row.ontology }}</code>
              </b-table-column>
              <b-table-column field="value" label="Value" v-slot="data">
                <pre v-if="typeof data.row.value === 'object'">{{ data.row.value }}</pre>
                <span v-else>{{ data.row.value }}</span>
              </b-table-column>
            </b-table>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

export default {
  components: {},
  data() {
    return {}
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    sketchAttributes() {
      let attributes = []
      for (let item in this.$store.state.meta.attributes) {
        attributes.push({
          name: item,
          ontology: this.$store.state.meta.attributes[item].ontology,
          value: this.$store.state.meta.attributes[item].value,
        })
      }
      return attributes
    },
  },
  mounted() {
    ApiClient.getSketchAttributes(this.sketch.id).then(response => {
      this.meta.attributes = response.data
    })
  },
}
</script>
