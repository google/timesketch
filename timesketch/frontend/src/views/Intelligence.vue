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

    <ts-navbar-secondary currentAppContext="sketch" currentPage="intelligence"></ts-navbar-secondary>
    <section class="section">
      <b-table v-if="intelligenceData.length > 0" :data="intelligenceData">
        <b-table-column field="type" label="IOC Type" v-slot="props">
          <code>{{ props.row.type }}</code>
        </b-table-column>

        <b-table-column field="ioc" label="Indicator data" v-slot="props">
          <router-link :to="{ name: 'Explore', query: generateQuery(props.row.ioc) }">
            <i class="fas fa-search" aria-hidden="true"></i>
          </router-link>
          <code>{{ props.row.ioc }}</code>
        </b-table-column>

        <b-table-column field="tags" label="Tags" v-slot="props">
          <b-taglist>
            <b-tag v-for="tag in props.row.tags" v-bind:key="tag" type="is-info is-light">{{ tag }} </b-tag>
          </b-taglist>
        </b-table-column>

        <b-table-column field="edit" label="" v-slot="props">
          Edit
        </b-table-column>

        <b-table-column field="delete" label="" v-slot="props">
          <span
            class="icon is-small"
            style="cursor:pointer;"
            title="Apply 'Exclude' filter"
            @click="deleteIoc(props.row)"
            ><i class="fas fa-trash"></i>
          </span>
        </b-table-column>
      </b-table>
      <div v-else class="card-content">
        Examine events in the <router-link :to="{ name: 'Explore' }">Explore view</router-link> to add intelligence
        locally
      </div>
    </section>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import _ from 'lodash'

export default {
  data() {
    return {}
  },
  methods: {
    deleteIoc(ioc) {
      var data = this.intelligenceData.filter(i => i.ioc !== ioc.ioc)
      ApiClient.addSketchAttribute(this.sketch.id, 'intelligence', { data: data }, 'intelligence').then(() => {
        this.loadIntelligence()
      })
    },
    loadIntelligence() {
      this.$store.dispatch('updateSketch', this.$store.state.sketch.id)
    },
    generateQuery(value) {
      let query = `"${value}"`
      return { q: query }
    },
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    intelligenceAttribute() {
      if (this.meta.attributes.intelligence === undefined) {
        return { ontology: 'intelligence', value: { data: [] }, name: 'intelligence' }
      }
      return this.meta.attributes.intelligence
    },
    intelligenceData() {
      return this.intelligenceAttribute.value.data
    },
  },
  mounted() {
    this.loadIntelligence()
  },
}
</script>
