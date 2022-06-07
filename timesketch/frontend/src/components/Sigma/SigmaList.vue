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
    <div class="container is-fluid">
      <b-table v-if="sketchTags.length > 0" :data="sketchTags">
        <b-table-column field="search" label="" v-slot="props" width="1em">
          <router-link
            :to="{ name: 'Explore', query: generateOpenSearchQuery(props.row.ts_sigma_rule, 'ts_sigma_rule') }">
            <i class="fas fa-search" aria-hidden="true"
              title="Search sketch for all events with this tag."></i>
          </router-link>
        </b-table-column>
        <b-table-column field="tag" label="Sigma rule name" v-slot="props"
          sortable>
          <b-tag type="is-info is-light">{{ props.row.ts_sigma_rule }}
          </b-tag>
        </b-table-column>
        <b-table-column field="count" label="Events tagged" v-slot="props"
          sortable numeric>
          {{ props.row.count }}
        </b-table-column>
        <b-table-column field="tag" label="Status of rule" v-slot="props"
          sortable>
          <b-tag
            :class="{ 'text-green': getRuleByName(props.row.ts_sigma_rule).result[0].ts_use_in_analyzer == true, 'text-red': getRuleByName(props.row.ts_sigma_rule).result[0].ts_use_in_analyzer == false }">
            {{
                getRuleByName(props.row.ts_sigma_rule).result[0].ts_use_in_analyzer
            }}
          </b-tag>
          <!--TODO(jaegeral): This needs to be backed with actual data-->
        </b-table-column>
      </b-table>
      <span v-else>No events have been tagged yet.</span>
    </div>
    <div class="container is-fluid">
      <b-table v-if="sketchTTP.length > 0" :data="sketchTTP">
        <b-table-column field="search" label="" v-slot="props" width="1em">
          <router-link
            :to="{ name: 'Explore', query: generateOpenSearchQuery(props.row.ts_ttp, 'ts_ttp') }">
            <i class="fas fa-search" aria-hidden="true"
              title="Search sketch for all events with this tag."></i>
          </router-link>
        </b-table-column>
        <b-table-column field="tag" label="TTP" v-slot="props" sortable>
          <b-tag type="is-info is-light">{{ props.row.ts_ttp }} </b-tag>
        </b-table-column>
        <b-table-column field="count" label="Events tagged" v-slot="props"
          sortable numeric>
          {{ props.row.count }}
        </b-table-column>
      </b-table>
      <span v-else>No events have been tagged yet.</span>
    </div>
    <div>
      <b-switch v-model="isComposed">Compose Sigma rule</b-switch>
      <div v-if="isComposed">
        <div class="container is-fluid">
          <div class="card">
            <div class="card-content"></div>
            <textarea id="textarea" v-model="text"
              placeholder="Enter your Sigma yaml File text..." rows="30"
              cols="80"></textarea>

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
      <b-table v-if="sigmaRuleList" :data="sigmaRuleList"
        :current-page.sync="currentPage" :per-page="perPage" detailed
        detail-key="title" paginated pagination-simple
        pagination-position="bottom" default-sort-direction="desc"
        sort-icon="arrow-down" sort-icon-size="is-small" icon-pack="fas"
        icon-prev="chevron-left" icon-next="chevron-right" default-sort="title"
        key="props.row.id">

        <b-table-column field="title" label="Name" v-slot="props" sortable
          searchable>
          <div @click="props.toggleDetails(props.row)"
            style="margin-top:5px;cursor:pointer;">
            {{ props.row.title }}
          </div>
        </b-table-column>

        <b-table-column field="ts_use_in_analyzer" label="Use in Analyzer"
          v-slot="props" sortable>
          <div @click="props.toggleDetails(props.row)"
            style="margin-top:5px;cursor:pointer;">
            {{ props.row.ts_use_in_analyzer }}
          </div>
        </b-table-column>

        <b-table-column field="description" label="Description" v-slot="props"
          searchable>
          <div @click="props.toggleDetails(props.row)"
            style="margin-top:5px;cursor:pointer;">
            {{ props.row.description }}
          </div>
        </b-table-column>

        <b-table-column field="author" label="Author" v-slot="props" searchable
          sortable>
          <div @click="props.toggleDetails(props.row)"
            style="margin-top:5px;cursor:pointer;">
            {{ props.row.author }}
          </div>
        </b-table-column>

        <b-table-column field="actions" label="" v-slot="props">
          <router-link
            :to="{ name: 'Explore', query: { q: props.row.es_query } }">
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
      sketchTags: [],
      sketchTTP: [],
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
  mounted() {
    this.loadSketchSigmaTags()
    this.loadSketchTTP()
  },
  methods: {
    parseSigma: function (event) {
      ApiClient.getSigmaByText(this.text)
        .then(response => {
          let SigmaRule = response.data.objects[0]
          this.parsed = SigmaRule
        })
        .catch(e => { })
    },
    loadSketchSigmaTags() {
      ApiClient.runAggregator(this.sketch.id, {
        aggregator_name: 'field_bucket',
        aggregator_parameters: { field: 'ts_sigma_rule' },
      }).then((response) => {
        this.sketchTags = response.data.objects[0].field_bucket.buckets
        // of the form [{count: 0, tag: 'foo'}]
      })
    },
    loadSketchTTP() {
      ApiClient.runAggregator(this.sketch.id, {
        aggregator_name: 'field_bucket',
        aggregator_parameters: { field: 'ts_ttp' },
      }).then((response) => {
        this.sketchTTP = response.data.objects[0].field_bucket.buckets
        // of the form [{count: 0, tag: 'foo'}]
      })
    },
    generateOpenSearchQuery(value, field) {
      let query = `"${value}"`
      // Escape special OpenSearch characters: \, [space]
      query = query.replace(/[\\\s]/g, '\\$&')
      if (field !== undefined) {
        query = `${field}:${query}`
      }
      return { q: query }
    },
    getRuleByName(ruleName) {
      var result = this.$store.state.sigmaRuleList.filter(obj => {
        return obj.file_name === ruleName
      })
      return { result }
    },
    getColor(status) {
      if (status === 'false') return "red"

      return "green";
    }
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

  .text-red {
    color: red;
  }

  .text-green {
    color: green;
  }
}
</style>
