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

    <b-modal :active.sync="showEditModal">
      <section class="box">
        <h1 class="subtitle">Edit Sigma Rule</h1>
        <b-field label="Edit Sigma Rule" label-position="on-border">
          <b-input custom-class="ioc-input" type="textarea" rows="30"
            v-model="editingRule.rule_yaml"></b-input>
        </b-field>
        <b-field grouped>
          Status: {{ editingRule.status }}
          <b-field grouped expanded position="is-right">
            <p class="control">
              <b-button type="is-primary"
                @click="parseSigma(editingRule.rule_yaml)">
                Parse
              </b-button>
            </p>
            <b-select placeholder="Rule status" v-model="editingRule.status"
              label="Rule status" label-position="on-border">
              <option v-for="option in RuleStatus" :value="option"
                :key="option">
                {{ option }}
              </option>
            </b-select>
            <p class="control">
              <b-button type="is-primary" @click="saveSigmaRule(editingRule)">
                Save
              </b-button>
            </p>
            <p class="control">
              <b-button @click="showEditModal = false">Cancel</b-button>
            </p>
          </b-field>
        </b-field>
        Parsed rule:
        <b>{{ parsed['es_query'] }}</b>
      </section>
    </b-modal>
    <!-- End modal -->

    <span class="icon is-small" style="cursor: pointer" title="Add a rule Rule"
      @click="composeRule()"><i class="fas fa-plus"></i>Add
    </span>

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

      <!-- This feature might be deprecated later
      <b-table-column field="ts_use_in_analyzer" label="Use in Analyzer2"
        v-slot="props" sortable>
        <div @click="props.toggleDetails(props.row)"
          style="margin-top:5px;cursor:pointer;">
          {{ props.row.ts_use_in_analyzer }}
        </div>
      </b-table-column>
      -->
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
          <i class="fas fa-search" aria-hidden="true"
            title="Search sketch for all events with this tag."></i>
        </router-link>
        {{ props.row.es_query }}
        <explore-preview style="margin-left: 10px"
          :searchQuery="props.row.es_query">
        </explore-preview>

        <span class="icon is-small" style="cursor: pointer" title="Edit Rule"
          @click="startRuleEdit(props.row)"><i class="fas fa-edit"></i>
        </span>

        <span class="icon is-small delete-ioc" style="cursor: pointer"
          title="Delete Rule" @click="deleteRule(props.row)"><i
            class="fas fa-trash"></i>
        </span>
      </b-table-column>

      <template #detail="props">
        <b>{{ props['row']['es_query'] }}</b>

        <pre>{{ JSON.stringify(props['row'], null, 2) }}</pre>
      </template>
    </b-table>

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
          <explore-preview style="margin-left: 10px"
            :searchQuery="generateOpenSearchQuery(props.row.ts_ttp, 'ts_ttp')">
          </explore-preview>
        </b-table-column>
      </b-table>
      <span v-else>No events have been tagged yet.</span>
    </div>

  </div>

</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import ExplorePreview from '../../components/Common/ExplorePreview'
export default {
  components: { ExplorePreview },
  data() {
    return {
      currentPage: 1,
      ascending: false,
      sortColumn: '',
      perPage: 10,
      editingRule: {},
      showEditModal: false,
      sketchTags: [],
      sketchTTP: [],
      analyses: [],
      RuleStatus: ["new", "deactivated"],
      text: `title: Suspicious Installation of ZMap
id: 5266a592-b793-11ea-b3de-0242ac130004
description: Detects suspicious installation of ZMap
references:
    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html
author: Alexander Jaeger
date: 2020/06/26
modified: 2020/06/26
tags:
    - attack.discovery
    - attack.t1046
logsource:
    product: linux
    service: shell
detection:
    keywords:
        # Generic suspicious commands
        - '*apt-get install zmap*'
    condition: keywords
falsepositives:
    - Unknown
level: high`,
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
  created() {
    if (this.timeline) {
      ApiClient.getSketchTimelineAnalysis(this.sketch.id, this.timeline.id)
        .then(response => {
          this.analyses = response.data.objects[0]
        })
        .catch(e => { })
    }
    // If no timeline was specified then loop over all of them
    else {
      this.sketch.timelines.forEach(timeline => {
        ApiClient.getSketchTimelineAnalysis(this.sketch.id, timeline.id)
          .then(response => {
            this.analyses = this.analyses.concat(response.data.objects[0])
          })
          .catch(e => { })
      })
    }
  },
  mounted() {
    this.loadSketchSigmaTags()
    this.loadSketchTTP()
  },
  methods: {
    parseSigma: function (rule_yaml) { // eslint-disable-line
      ApiClient.getSigmaByText(rule_yaml)
        .then(response => {
          let SigmaRule = response.data.objects[0]
          this.parsed = SigmaRule
        })
        .catch(e => { })
    },
    addRule: function (event) {
      ApiClient.createSigmaRule(this.text).then(response => {
        let SigmaRule = response.data.objects[0]
        this.parsed = SigmaRule
      })
    },
    composeRule(rule) {
      this.showEditModal = true
      this.editingRule = { rule_yaml: this.text }
    },
    startRuleEdit(rule) {
      if (rule === null)
        console.log("No rule given, maybe you wanna add one?")
      this.showEditModal = true
      this.editingRule = rule
    },
    saveSigmaRule(rule) {
      console.log("save Sigma Rule")
      console.log(rule)
      ApiClient.updateSigmaRule(rule.id, rule.rule_yaml, rule.rule_uuid)
        .then(response => { })
        .catch(e => {
          console.error(e)
        })
      this.$buefy.notification.open({ message: 'Succesfully added Sigma rule!', type: 'is-success' })
      this.showEditModal = false
    },
    deleteRule(ioc) {
      if (confirm('Delete Rule?')) {
        ApiClient.deleteSigmaRule(ioc.rule_uuid)
          .then(response => { })
          .catch(e => {
            console.error(e)
          })
        // remove the element from the array
      }
      location.reload();
    },
    generateOpenSearchQuery(value, field) {
      console.log("Looking for" + value + " in " + field)
      let query = `"${value}"`
      // Escape special OpenSearch characters: \, [space]
      query = query.replace(/[\\\s]/g, '\\$&')
      if (field !== undefined) {
        query = `${field}:${query}`
      }
      return { q: query }
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
    getColor(status) {
      if (status === 'false') return "red"
      return "green";
    },
    getRuleByUUID(rule_uuid) {
      if (Array.isArray(this.$store.state.sigmaRuleList)) {
        console.log("trying to find" + rule_uuid)
        var result = this.$store.state.sigmaRuleList.filter(obj => {
          return obj.rule_uuid === rule_uuid
        })
        return { result }
      } else {
        console.log(rule_uuid + 'is not found');
        return {
          // If not found in the current installed rules
          result: [{
            "file_name": ruleName, "ts_use_in_analyzer": "Not found",
          }]
        }
      }
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

  .text-red {
    color: red;
  }

  .text-green {
    color: green;
  }
}
</style>
