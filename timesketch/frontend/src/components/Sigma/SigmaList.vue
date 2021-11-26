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
    <b-table
      v-if="sigmaRuleList"
      :data="sigmaRuleList"
      :current-page.sync="currentPage"
      :per-page="perPage"
      detailed
      detail-key="title"
      paginated
      pagination-simple
      pagination-position="bottom"
      default-sort-direction="desc"
      sort-icon="arrow-down"
      sort-icon-size="is-small"
      icon-pack="fas"
      icon-prev="chevron-left"
      icon-next="chevron-right"
      default-sort="title"
      key="props.row.id"
    >
      <b-switch v-model="isComposed">Compose Sigma rule</b-switch>
      <div v-if="isComposed">
        <div class="container is-fluid">
          <div class="card">
            <div class="card-content"></div>
            <textarea
              id="textarea"
              v-model="text"
              placeholder="Enter your Sigma yaml File text..."
              rows="30"
              cols="80"
            ></textarea>

            <div class="control">
              <button id="parseButton" v-on:click="parseSigma">Parse</button>
            </div>
            <template>
              <b>Clean ES Query: {{ parsed['es_query'] }}</b>
              <pre>{{ JSON.stringify(parsed, null, 2) }}</pre>
            </template>
          </div>
        </div>
      </div>
      <b-table-column field="title" label="Name" v-slot="props" sortable searchable>
        <div @click="props.toggleDetails(props.row)" style="margin-top:5px;cursor:pointer;">
          {{ props.row.title }}
        </div>
      </b-table-column>

      <b-table-column field="description" label="Description" v-slot="props" searchable>
        <div @click="props.toggleDetails(props.row)" style="margin-top:5px;cursor:pointer;">
          {{ props.row.description }}
        </div>
      </b-table-column>

      <b-table-column field="actions" label="" v-slot="props">
        <router-link :to="{ name: 'Explore', query: { q: props.row.es_query } }">
          <button class="button is-outlined" style="float:right;">
            <span class="icon is-small" style="margin-right:7px">
              <i class="fas fa-search"></i>
            </span>
            Search
          </button>
        </router-link>
      </b-table-column>

      <template #detail="props">
        <b>{{ props['row']['es_query'] }}</b>

        <pre>{{ JSON.stringify(props['row'], null, 2) }}</pre>
      </template>
    </b-table>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  data() {
    return {
      currentPage: 1,
      ascending: false,
      sortColumn: '',
      perPage: 10,
      isComposed: false,
      text: `Place your Sigma rule here and press parse`,
      parsed: '',
    }
  },
  computed: {
    sigmaRuleList() {
      return this.$store.state.sigmaRuleList
    },
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  methods: {
    parseSigma: function(event) {
      ApiClient.getSigmaByText(this.text)
        .then(response => {
          let SigmaRule = response.data.objects[0]
          this.parsed = SigmaRule
        })
        .catch(e => {})
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
pre {
  white-space: pre-wrap;
  white-space: -moz-pre-wrap;
  white-space: -pre-wrap;
  white-space: -o-pre-wrap;
  word-wrap: break-word;
}
</style>
