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

          <b-field grouped expanded position="is-right">
            <p class="control">
              <b-button type="is-primary"
                @click="parseSigma(editingRule.rule_yaml)">
                Parse
              </b-button>
            </p>
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
      @click="composeRule()"><i class="fas fa-edit"></i>
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
  methods: {
    parseSigma: function (rule_yaml) {
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
    onEditTitle(e) {
      console.log(e.target.innerText)
      this.sketch.name = e.target.innerText
      this.saveSigmaRule()
    },
    onEditYAML(e) {
      console.log(e)
      //console.log(this._data.props)
      //this.sketch.name = e.target.innerText
      //this.saveSigmaRule(e)
    },
    onEditAuthor(e) {
      console.log(e.target.innerText)
      this.sketch.description = e.target.innerText
      this.saveSigmaRule(e)
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
        //var data = this.intelligenceData.filter((i) => i.ioc !== ioc.ioc)
        //ApiClient.addSketchAttribute(this.sketch.id, 'intelligence', { data: data }, 'intelligence').then(() => {
        //  this.loadSketchAttributes()
        //})
        ApiClient.deleteSigmaRule(ioc.rule_uuid)
          .then(response => { })
          .catch(e => {
            console.error(e)
          })
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
}
</style>
