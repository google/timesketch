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
        <div style="width: 100%;">
          <div style="width: 50%; height: 80px; float: left;">
            <h2>Templates</h2>
            <b-select placeholder="Templates" v-model="editingRule.rule_yaml"
              label="Templates" label-position="on-border">
              <option v-for="template in SigmaTemplates" :value="template.text"
                :key="template.os">
                {{ template.os }}
              </option>
            </b-select>
          </div>
          <div style="margin-left: 50%; height: 80px;">
            <div>Parsed rule Search query:
              <b><code>{{ parsed['search_query'] }}</code></b>
              <explore-preview :searchQuery="parsed['search_query']">
              </explore-preview>
            </div>

            <div>Parsing Status: {{problemString}}</div>
          </div>
        </div>
        <b-field label="Edit Sigma Rule" label-position="on-border"
          style="margin-top: 25px;">
          <b-input custom-class="ioc-input" type="textarea" rows="25"
            v-model="editingRule.rule_yaml"
            @input="parseSigma(editingRule.rule_yaml)"></b-input>
        </b-field>
        <b-field grouped>
          <b-field grouped expanded position="is-right">
            <p class="control">
              <b-button :disabled="problemString.toLowerCase() !== 'ok'"
                type="is-primary" @click="addOrUpdateRule(editingRule)">
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
        <div @click="startRuleEdit(props.row)" custom-class="margintop-pointer">
          {{ props.row.title }}
        </div>
      </b-table-column>

      <b-table-column field="author" label="Author" v-slot="props" searchable
        sortable>
        <div @click="startRuleEdit(props.row)" custom-class="margintop-pointer">
          {{ props.row.author }}
        </div>

      </b-table-column>
      <b-table-column field="status" label="Status" v-slot="props" sortable
        searchable>
        <div @click="startRuleEdit(props.row)" custom-class="margintop-pointer">
          {{ props.row.status }} <span class="icon is-small"
            custom-class="clickable"
            title="Only stable rules are used in the Sigma Analyzer"><i
              class="fas fa-info-circle"
              v-if="props.row.status != 'stable'"></i>
          </span>
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

        <span class="icon is-small" custom-class="clickable" title="Edit Rule"
          @click="startRuleEdit(props.row)"><i class="fas fa-edit"></i>
        </span>
        <span class="icon is-small" custom-class="clickable" title="Delete Rule"
          @click="deleteRule(props.row)"><i class="fas fa-trash"></i>
        </span>
      </b-table-column>
    </b-table>
    <div class="container is-fluid">
      <b-table v-if="sketchTTP.length > 0" :data="sketchTTP">
        <b-table-column field="search" label="" v-slot="props" width="1em">
          <router-link :to="{
          name: 'Explore',
          query: generateOpenSearchQuery(props.row.ts_ttp, 'ts_ttp') }">
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
      SigmaTemplates: SigmaTemplates,
      text: '',
      parsed: '',
      problemString: 'Ok',
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
    // Set debounce to 300ms if parseSigma is used.
    parseSigma: _.debounce(function (rule_yaml) { // eslint-disable-line
      this.problemString = ''
      ApiClient.getSigmaRuleByText(rule_yaml)
        .then(response => {
          this.parsed = response.data.objects[0]
          this.problemString = 'OK'
        })
        .catch(e => {
          this.problemString = e.response.data.message
          // need to set search_query to something, to overwrite previous value
          this.parsed['search_query'] = 'PLEASE ADJUST RULE'
          Snackbar.open({
            message: this.problemString,
            type: 'is-danger',
            position: 'is-top',
            indefinite: false,
          })
        })
    }, 300),
    addOrUpdateRule: function (event) {
      if (this.save_button_text === "Create") {
        ApiClient.createSigmaRule(this.editingRule.rule_yaml).then(response => {
          this.$buefy.notification.open({
            message: 'Succesfully added Sigma rule!',
            type: 'is-success'
          })
          this.showEditModal = false
          this.sigmaRuleList.push(response.data.objects[0])
        })
          .catch(e => {
            this.problemString = this.problemString = e.response.data.message
            Snackbar.open({
              message: this.problemString,
              type: 'is-danger',
              position: 'is-top',
              indefinite: false,
            })
          })
      }
      if (this.save_button_text === "Update") {
        ApiClient.updateSigmaRule(this.editingRule.id, this.editingRule.rule_yaml)
          .then(response => {
            this.$store.state.sigmaRuleList = this.sigmaRuleList.filter(obj => {
              return obj.rule_uuid !== this.editingRule.rule_uuid
            })
            this.sigmaRuleList.push(response.data.objects[0])
            // do not close the the edit view in case there is an error
            this.$buefy.notification.open(
              {
                message: 'Succesfully modified Sigma rule!',
                type: 'is-success'
              })
            this.showEditModal = false
          })
          .catch(e => {
          })
      }
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
          .then(response => {
            // remove element from Array
            this.$store.state.sigmaRuleList = this.sigmaRuleList.filter(obj => {
              return obj.rule_uuid !== ioc.rule_uuid
            })
          })
          .catch(e => {
            console.error(e)
          })
      }
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
          return obj.rule_uuid === ruleUuid
        })
        return { result }
      } else {
        return {
          // If not found in the current installed rules
          result: [{
            "rule_uuid": ruleUuid,
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

  .margintop-pointer {
    margin-top: 5px;
    cursor: pointer;
  }

  .clickable {
    cursor: pointer
  }
}
</style>