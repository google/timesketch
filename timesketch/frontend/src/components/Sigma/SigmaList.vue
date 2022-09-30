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
        <h1 class="subtitle">{{save_button_text}} Sigma Rule</h1>
        <h2>Templates</h2>
        <b-select placeholder="Templates" v-model="editingRule.rule_yaml"
          label="Templates" label-position="on-border">
          <option v-for="template in SigmaTemplates" :value="template.text"
            :key="template.os">
            {{ template.os }}
          </option>
        </b-select>
        Parsed rule Search query:
        <b><code>{{ parsed['search_query'] }}</code></b>
        <explore-preview :searchQuery="parsed['search_query']">
        </explore-preview>

        <b-field label="Edit Sigma Rule" label-position="on-border"
          style="margin-top: 25px;">
          <b-input custom-class="ioc-input" type="textarea" rows="25"
            v-model="editingRule.rule_yaml"
            @input="parseSigma(editingRule.rule_yaml)"></b-input>
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
              <b-button type="is-primary" @click="addRule(editingRule)">
                {{save_button_text}}
              </b-button>
            </p>
            <p class="control">
              <b-button @click="showEditModal = false">Cancel</b-button>
            </p>
          </b-field>
        </b-field>

      </section>
    </b-modal>
    <!-- End modal -->

    <span class="icon is-small" style="cursor: pointer" title="Add a rule Rule"
      @click="composeRule()"><i class="fas fa-plus"></i>Add
    </span>

    <b-table v-if="sigmaRuleList" :data="sigmaRuleList"
      :current-page.sync="currentPage" :per-page="perPage" paginated
      pagination-simple pagination-position="bottom"
      default-sort-direction="desc" sort-icon="arrow-down"
      sort-icon-size="is-small" icon-pack="fas" icon-prev="chevron-left"
      icon-next="chevron-right" default-sort="title" key="props.row.id">

      <b-table-column field="title" label="Name" v-slot="props" sortable
        searchable>
        <div @click="startRuleEdit(props.row)"
          style="margin-top:5px;cursor:pointer;">
          {{ props.row.title }}
        </div>
      </b-table-column>

      <b-table-column field="author" label="Author" v-slot="props" searchable
        sortable>
        <div @click="startRuleEdit(props.row)"
          style="margin-top:5px;cursor:pointer;">
          {{ props.row.author }}
        </div>

      </b-table-column>
      <b-table-column field="status" label="Status" v-slot="props" sortable
        searchable>
        <div @click="startRuleEdit(props.row)"
          style="margin-top:5px;cursor:pointer;">
          {{ props.row.status }} <span class="icon is-small"
            style="cursor: pointer"
            title="Only stable will be used in Sigma Analyzer"><i
              class="fas fa-info-circle"
              v-if="props.row.status != 'stable'"></i>
          </span>
        </div>
      </b-table-column>

      <b-table-column field="title" label="Name" v-slot="props" sortable
        searchable>
        <div @click="startRuleEdit(props.row)"
          style="margin-top:5px;cursor:pointer;">
          {{ props.row.title }}
        </div>
      </b-table-column>

      <b-table-column field="actions" label="Actions" v-slot="props">
        <router-link
          :to="{ name: 'Explore', query: { q: props.row.search_query } }">
          <i class="fas fa-search" aria-hidden="true"
            title="Search sketch for all events with this tag."></i>
        </router-link>

        <explore-preview style="margin-left: 10px"
          :searchQuery="props.row.search_query">
        </explore-preview>

        <span class="icon is-small" style="cursor: pointer" title="Edit Rule"
          @click="startRuleEdit(props.row)"><i class="fas fa-edit"></i>
        </span>
        <span class="icon is-small" style="cursor: pointer" title="Delete Rule"
          @click="deleteRule(props.row)"><i class="fas fa-trash"></i>
        </span>
      </b-table-column>
      <b-table-column field="title" label="Search Query" v-slot="props">
        {{ props.row.search_query }}</b-table-column>
      <b-table-column field="title" label="Warnings" v-slot="props">
        {{ problemDetector(props.row.search_query) }}</b-table-column>


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
          <explore-preview style="margin-left: 10px"
            :searchQuery="props.row.ts_ttp">
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
import { SnackbarProgrammatic as Snackbar } from 'buefy'
import { SigmaTemplates } from '@/utils/SigmaRuleTemplates'
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
      save_button_text: "Update", // false: update rule. true: create new in DB
      sketchTags: [],
      sketchTTP: [],
      analyses: [],
      SigmaTemplates: SigmaTemplates,
      ruleStatus: ["stable", "test", "experimental", "deprecated", "unsupported"],
      text: '',
      parsed: '',
      dataTypePresent: false,
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
    problemDetector: function (searchQuery) {// eslint-disable-line
      let reason = "OK"
      if (!searchQuery.includes("data_type") || searchQuery.includes("source_name")) {
        reason = ("No data_type or source_name defined in the rule consider add field mappings in the sigma config file")
      }
      if (searchQuery.length < 10) {
        reason.concat("Query seems very short. It might return a lot of events and be to broad.")
      }
      return reason
    },
    parseSigma: function (rule_yaml) { // eslint-disable-line
      this.parsing_issues = []
      ApiClient.getSigmaRuleByText(rule_yaml)
        .then(response => {
          let SigmaRule = response.data.objects[0]
          this.parsed = SigmaRule
          this.dataTypePresent = (SigmaRule['search_query'].includes("data_type") || SigmaRule['search_query'].includes("source_name"))

        })
        .catch(e => {
          Snackbar.open({
            message: 'Sigma rule parsing failed. See Browser console for more',
            type: 'is-danger',
            position: 'is-top',
            indefinite: false,
          })
        })
    },
    addRule: function (event) {
      this.parseSigma(this.editingRule.rule_yaml)
      if (this.save_button_text === "Create") {
        ApiClient.getSigmaRuleByText(this.editingRule.rule_yaml)
          .then(response => {
            let SigmaRule = response.data.objects[0]
            this.parsed = SigmaRule
            this.dataTypePresent = (SigmaRule['search_query'].includes("data_type") || SigmaRule['search_query'].includes("source_name"))
            ApiClient.createSigmaRule(this.editingRule.rule_yaml).then(response => {
              location.reload();
              this.$buefy.notification.open({ message: 'Succesfully added Sigma rule!', type: 'is-success' })
              this.showEditModal = false
            })
              .catch(e => {
                console.error(e)
              })
          })
          .catch(e => {
          })
      }
      if (this.save_button_text === "Update") {
        // Only update the rule if the parsing was positive.
        ApiClient.getSigmaRuleByText(this.editingRule.rule_yaml)
          .then(response => {
            let SigmaRule = response.data.objects[0]
            this.parsed = SigmaRule
            ApiClient.updateSigmaRule(this.editingRule.id, this.editingRule.rule_yaml)
              .then(response => { })
              .catch(e => {
                console.error(e)
              })
            location.reload();
            this.$buefy.notification.open({ message: 'Succesfully modified Sigma rule!', type: 'is-success' })
            this.showEditModal = false
            this.dataTypePresent = (SigmaRule['search_query'].includes("data_type") || SigmaRule['search_query'].includes("source_name"))
          })
          .catch(e => {
          })
      }
      //
    },
    composeRule() {
      this.showEditModal = true
      this.create_new_rule = true
      this.save_button_text = "Create"
      this.editingRule = { rule_yaml: this.text }
    },
    startRuleEdit(rule) {
      if (rule === null)
        console.log("No rule given, maybe you wanna add one?")
      this.save_button_text = "Update"
      this.showEditModal = true
      this.editingRule = rule
    },
    deleteRule(ioc) {
      if (confirm('Delete Rule?')) {
        ApiClient.deleteSigmaRule(ioc.rule_uuid)
          .then(response => { })
          .catch(e => {
            console.error(e)
          })
        // TODO: remove the element from the array
      }
      // instead of removing the element from the array gonna relad the page
      location.reload();
    },
    generateOpenSearchQuery(value, field) {
      let query = `"${value}"`
      // Escape special OpenSearch characters: \, [space]
      query = query.replace(/[\\\s]/g, '\\$&')
      if (field !== undefined) {
        query = `${field}: ${query}`
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
    getColorFromStatus(status) {
      if (status === 'false') return "red"
      return "green";
    },
    getRuleByUUID(ruleUuid) {
      if (Array.isArray(this.$store.state.sigmaRuleList)) {
        var result = this.$store.state.sigmaRuleList.filter(obj => {
          return obj.rule_uuid === RuleUuid
        })
        return { result }
      } else {
        return {
          // If not found in the current installed rules
          result: [{
            "rule_uuid": RuleUuid,
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