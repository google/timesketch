<!--
Copyright 2023 Google Inc. All rights reserved.

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
    <v-toolbar dense flat class="mt-n3 ml-n4" color="transparent">
      <v-toolbar-title v-if="!editingRule.title"> Create new rule</v-toolbar-title>
      <v-toolbar-title v-else> {{ editingRule.title }}</v-toolbar-title>
    </v-toolbar>
    <v-autocomplete
      v-if="!ruleId"
      align="left"
      dense
      outlined
      hide-details
      :items="SigmaTemplates"
      @change="selectTemplate"
      item-text="title"
      label="Choose template"
      style="width: 300px"
      class="mb-4 mt-2"
    >
    </v-autocomplete>

    <div v-if="editingRule.search_query">
      <v-alert type="error" outlined dense v-if="!isParsingSuccesful && status_text">
        {{ status_text }}
      </v-alert>
      <v-alert type="success" v-else outlined dense>
        Preview:
        <span style="font-family: monospace">{{ editingRule.search_query }}</span>
      </v-alert>
    </div>

    <v-card outlined>
      <v-textarea
        v-model="ruleYamlTextArea"
        solo
        flat
        hide-details
        rows="25"
        autofocus
        placeholder="Get started by choosing a template above.."
        @input="parseSigma(ruleYamlTextArea)"
        :color="this.isParsingSuccesful ? 'success' : 'error'"
        class="editSigmaRule"
      >
      </v-textarea>
      <v-divider></v-divider>
      <v-card-actions>
        <v-btn :disabled="!isParsingSuccesful" @click="saveRule()" text color="primary"> Save </v-btn>
        <v-btn text :to="{ name: 'Explore' }" style="margin-left: 10px"> Cancel </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import { SigmaTemplates, defaultSigmaPlaceholder } from '@/utils/SigmaRuleTemplates'
import _ from 'lodash'

export default {
  props: {
    ruleId: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      editingRule: {},
      status_text: '',
      ruleYamlTextArea: '',
      SigmaTemplates: SigmaTemplates,
      search: '',
      isParsingSuccesful: false,
    }
  },
  methods: {
    selectTemplate(text) {
      var matchingTemplate = this.SigmaTemplates.find((obj) => {
        return obj.title === text
      })
      this.ruleYamlTextArea = matchingTemplate.text
      this.parseSigma(matchingTemplate.text)
    },
    parseSigma: _.debounce(function (ruleYaml) {
      if (!ruleYaml) {
        this.editingRule.search_query = ''
        return
      }
      ApiClient.getSigmaRuleByText(ruleYaml)
        .then((response) => {
          var parsedRule = response.data.objects[0]
          if (parsedRule.tags.length > 0 && parsedRule.tags[0] == null) {
            this.status_text = 'Please specify at least one tag if you use the tags field'
            this.isParsingSuccesful = false
          } else if (!parsedRule.author) {
            this.status_text = 'No author specified'
            this.isParsingSuccesful = false
          } else {
            this.editingRule = parsedRule
            this.isParsingSuccesful = true
            this.status_text = ''
          }
        })
        .catch((e) => {
          this.status_text = e.response.data.message
          this.isParsingSuccesful = false
        })
    }, 300),
    getRuleByUUID(ruleUuid) {
      if (!ruleUuid) {
        return
      }
      ApiClient.getSigmaRuleResource(ruleUuid)
        .then((response) => {
          this.editingRule = response.data.objects[0]
          this.ruleYamlTextArea = this.editingRule.rule_yaml // eslint-disable-line camelcase
          this.isParsingSuccesful = true
        })
        .catch((e) => {
          console.error(e)
          this.isParsingSuccesful = false
          this.ruleYamlTextArea = defaultSigmaPlaceholder
          this.parseSigma(this.ruleYamlTextArea)
        })
    },
    deleteRule(ruleUuid) {
      if (confirm('Delete Rule?')) {
        ApiClient.deleteSigmaRule(ruleUuid)
          .then((response) => {
            this.$store.dispatch('updateSigmaList')
            this.successSnackBar('Rule deleted!')
          })
          .catch((e) => {
            this.errorSnackBar('Error deleting rule: ' + ruleUuid)
            console.error(e)
          })
      }
    },
    saveRule: function () {
      // Create new rule
      if (!this.ruleId) {
        ApiClient.createSigmaRule(this.ruleYamlTextArea)
          .then(() => {
            this.$store.dispatch('updateSigmaList')
            this.successSnackBar('Rule created: ' + this.editingRule.title)
          })
          .catch((e) => {
            this.errorSnackBar('Error creating rule: ' + this.editingRule.title)
            console.error(e)
          })
        return
      }
      // Update existing rule
      ApiClient.updateSigmaRule(this.editingRule.id, this.ruleYamlTextArea)
        .then(() => {
          this.$store.dispatch('updateSigmaList')
          this.successSnackBar('Rule updated: ' + this.editingRule.title)
        })
        .catch((e) => {
          this.errorSnackBar('Error updating rule: ' + this.editingRule.title)
          console.error(e)
        })
    },
  },
  mounted() {
    if (this.ruleId) {
      this.getRuleByUUID(this.ruleId)
    }
  },
  watch: {
    ruleId: function (newRuleId) {
      if (newRuleId) {
        this.getRuleByUUID(newRuleId)
      }
    },
  },
}
</script>

<style scoped lang="scss">
.editSigmaRule {
  font-family: monospace;
  font-size: 13px;
}
</style>
