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
  <v-container class="px-8">
    <h2>
      {{ editingRule.title }}
      <v-chip rounded x-small class="mr-2" :color="statusColors()">
        <v-icon v-if="isParsingSuccesful" x-small> mdi-check </v-icon>
        <v-icon v-else x-small> mdi-alert </v-icon>
        Error</v-chip
      >
    </h2>

    <div>
      <v-autocomplete dense filled rounded :items="SigmaTemplates" @change="selectTemplate" item-text="title">
      </v-autocomplete>
    </div>
    <div class="alertbox" v-if="!isParsingSuccesful">
      <v-alert dense type="error">
        {{ status_text }}
      </v-alert>
    </div>

    <v-textarea
      label="Edit Sigma rule"
      outlined
      :color="statusColors()"
      autocomplete="email"
      rows="25"
      v-model="ruleYamlTextArea"
      background-color="statusColors()"
      @input="parseSigma(ruleYamlTextArea)"
      class="editSigmaRule"
    >
    </v-textarea>

    <div class="alertbox" v-if="isParsingSuccesful">
      <v-alert colored-border border="left" elevation="1" :color="statusColors()">
        <b>Search Query:</b>
        {{ editingRule.search_query }}
      </v-alert>
    </div>

    <div class="mt-3">
      <v-btn :disabled="!isParsingSuccesful" @click="addOrUpdateRule(ruleYamlTextArea)" small depressed color="primary">
        {{ isNewRule ? 'Create Rule' : 'Update Rule' }}
      </v-btn>
      <div style="width: 20px; display: inline-block"></div>
      <v-btn @click="$router.back()" small depressed color="secondary">Cancel </v-btn>
      <!-- make 20 px space° -->
      <div style="width: 20px; display: inline-block"></div>
      <v-btn @click="deleteRule(rule_uuid)" small depressed color="red" :disabled="isNewRule">Delete Rule</v-btn>
    </div>
  </v-container>
</template>
  
<script>
import ApiClient from '../../utils/RestApiClient'
import { SigmaTemplates, defaultSigmaPlaceholder } from '@/utils/SigmaRuleTemplates'
import EventBus from '../../main'
import _ from 'lodash'

export default {
  props: ['rule_uuid', 'sigmaRule'],
  data() {
    return {
      editingRule: { ruleYaml: 'foobar' }, // empty state
      status_chip_text: 'OK',
      status_text: '',
      ruleYamlTextArea: {},
      SigmaTemplates: SigmaTemplates,
      search: '',
      isNewRule: false,
      isUpdatingRule: false,
      isParsingSuccesful: false,
    }
  },
  watch: {
    rule_uuid: function (newVal, oldVal) {
      this.getRuleByUUID(newVal)
    },
  },
  loaded() {
    console.log('loaded')
    this.parseSigma(this.editingRule.rule_yaml)
  },
  mounted() {
    console.log('mounted')
    // check if router was called with sigma/new
    if (this.rule_uuid === 'new') {
      this.editingRule = {
        title: 'New Sigma Rule',
      }
      this.isNewRule = true
      this.isUpdatingRule = false
      this.status_chip_text = 'OK'
      this.ruleYaml = defaultSigmaPlaceholder
      this.editingRule.rule_yaml = defaultSigmaPlaceholder
      this.parseSigma(this.editingRule.rule_yaml)
    }

    this.getRuleByUUID(this.rule_uuid)
  },
  methods: {
    selectTemplate(text) {
      var matchingTemplate = this.SigmaTemplates.find((obj) => {
        return obj.title === text
      })
      this.ruleYamlTextArea = matchingTemplate.text
      this.parseSigma(matchingTemplate.text)
    },
    // Set debounce to 300ms if parseSigma is used.
    parseSigma: _.debounce(function (ruleYaml) {
      console.log('parseSigma with ' + ruleYaml)
      console.log('maybe use insted ' + this.editingRule.rule_yaml)
      // eslint-disable-line
      ApiClient.getSigmaRuleByText(ruleYaml)
        .then((response) => {
          var parsedRule = response.data.objects[0]
          if (!parsedRule.author) {
            this.status_text = 'No Author given'
            this.isParsingSuccesful = false
          } else {
            this.editingRule = parsedRule
            this.isParsingSuccesful = true
            this.status_chip_text = 'Ok'
            this.status_text = ''
          }
        })
        .catch((e) => {
          this.status_text = e.response.data.message
          this.isParsingSuccesful = false
          this.status_chip_text = 'ERROR'
        })
    }, 300),
    statusColors() {
      if (this.isParsingSuccesful) {
        return 'success'
      }
      return 'error'
    },
    getRuleByUUID(ruleUuid) {
      ApiClient.getSigmaRuleResource(ruleUuid)
        .then((response) => {
          this.editingRule = response.data.objects[0]
          this.ruleYamlTextArea = this.editingRule.rule_yaml // eslint-disable-line camelcase
          this.status_chip_text = 'Ok'
          this.isNewRule = false
          this.isUpdatingRule = true
          this.isParsingSuccesful = true
        })
        .catch((e) => {
          console.error(e)
          this.isParsingSuccesful = false
          this.isNewRule = true
          this.isUpdatingRule = false
          this.ruleYamlTextArea = defaultSigmaPlaceholder
        })
    },
    deleteRule(ruleUuid) {
      if (confirm('Delete Rule?')) {
        ApiClient.deleteSigmaRule(ruleUuid)
          .then((response) => {
            console.log('Rule deleted: ' + ruleUuid)
            this.$store.dispatch('updateSigmaList')
            EventBus.$emit('errorSnackBar', 'Rule deleted: ' + ruleUuid)
          })
          .catch((e) => {
            console.error(e)
          })
      }
    },
    addOrUpdateRule: function (event) {
      if (this.isNewRule) {
        ApiClient.createSigmaRule(this.ruleYaml)
          .then((response) => {
            this.$store.dispatch('updateSigmaList')
            EventBus.$emit('errorSnackBar', 'Rule created: ' + this.editingRule.id)
          })
          .catch((e) => {
            console.error(e)
          })
      }
      if (this.isUpdatingRule) {
        ApiClient.updateSigmaRule(this.editingRule.id, this.ruleYaml)
          .then((response) => {
            this.$store.dispatch('updateSigmaList')
            EventBus.$emit('successSnackBar', 'Rule updated: ' + this.editingRule.id)
          })
          .catch((e) => {})
      }
    },
  },
}
</script>
  
<style scoped lang="scss">
.alertbox {
  width: 500;
}
.editSigmaRule {
  font-family: monospace;
}
pre {
  white-space: pre-wrap;
  /* Since CSS 2.1 */
  white-space: -moz-pre-wrap;
  /* Mozilla, since 1999 */
  white-space: -pre-wrap;
  /* Opera 4-6 */
  white-space: -o-pre-wrap;
  /* Opera 7 */
  word-wrap: break-word;
  /* Internet Explorer 5.5+ */
}
</style>