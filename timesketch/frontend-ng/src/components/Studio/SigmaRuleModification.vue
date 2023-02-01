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
  <v-container fluid>
    <div style="margin-bottom: 20px; margin-top: -55px">
      <!-- This is a very hacky way to move the whole content to the top,
      there is currently no global solution to get that depending on the context
      TODO(jaegeral): find a better solution with jbn
      -->
      <strong>
        {{ editingRule.title }}
        <v-chip rounded x-small class="ml-2" :color="this.isParsingSuccesful ? 'success' : 'error'">
          <v-icon v-if="isParsingSuccesful" x-small left> mdi-check </v-icon>
          <v-icon v-else x-small left> mdi-alert </v-icon>
          {{ isParsingSuccesful ? 'OK' : 'ERROR' }}</v-chip
        >
      </strong>
    </div>
    <div style="width: 250px">
      <v-autocomplete
        align="left"
        dense
        outlined
        :items="SigmaTemplates"
        @change="selectTemplate"
        item-text="title"
        label="Choose template"
      >
      </v-autocomplete>
    </div>
    <div class="alertbox" v-if="!isParsingSuccesful">
      <v-alert dense type="error" outlined>
        {{ status_text }}
      </v-alert>
    </div>

    <v-textarea
      label="Edit Sigma rule"
      outlined
      :color="this.isParsingSuccesful ? 'success' : 'error'"
      autocomplete="email"
      rows="23"
      v-model="ruleYamlTextArea"
      @input="parseSigma(ruleYamlTextArea)"
      class="editSigmaRule"
      hide-details
    >
    </v-textarea>

    <div class="mt-2">
      <v-btn :disabled="!isParsingSuccesful" @click="addOrUpdateRule(ruleYamlTextArea)" small depressed color="primary">
        {{ isNewRule ? 'Create Rule' : 'Update Rule' }}
      </v-btn>
      <v-btn color="primary" text @click="$router.back()" style="margin-left: 10px"> Cancel </v-btn>
      <v-btn v-show="!isNewRule" @click="deleteRule(rule_uuid)" small text color="error darken-2"
        ><v-icon>mdi-delete</v-icon></v-btn
      >
    </div>

    <div v-if="isParsingSuccesful" class="mt-5">
      <strong>Preview opensearch query:</strong>
      <pre>{{ editingRule.search_query }}</pre>
      <!-- TODO: This should become a global class how to nicely highlight a query -->
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
      editingRule: { ruleYaml: defaultSigmaPlaceholder }, // empty state
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
      if (newVal === 'new') {
        this.editingRule = {
          title: 'New Sigma Rule',
        }
        this.resetComponent()
      } else {
        this.getRuleByUUID(newVal)
      }
    },
  },
  loaded() {
    this.parseSigma(this.editingRule.rule_yaml)
  },
  mounted() {
    if (this.rule_uuid === 'new') {
      this.resetComponent()
    } else {
      this.getRuleByUUID(this.rule_uuid)
    }
  },
  methods: {
    resetComponent() {
      this.editingRule = {
        title: 'New Sigma Rule',
      }
      this.isNewRule = true
      this.isUpdatingRule = false
      this.isParsingSuccesful = true
      this.ruleYamlTextArea = defaultSigmaPlaceholder
      this.editingRule.rule_yaml = defaultSigmaPlaceholder
      this.parseSigma(this.editingRule.rule_yaml)
      this.rule_uuid = this.editingRule.rule_uuid
    },
    selectTemplate(text) {
      var matchingTemplate = this.SigmaTemplates.find((obj) => {
        return obj.title === text
      })
      this.ruleYamlTextArea = matchingTemplate.text
      this.parseSigma(matchingTemplate.text)
    },
    // Set debounce to 300ms if parseSigma is used.
    parseSigma: _.debounce(function (ruleYaml) {
      // eslint-disable-line
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
            this.rule_uuid = parsedRule.uuid
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
      if (ruleUuid === 'new' || ruleUuid === undefined) {
        return
      }
      ApiClient.getSigmaRuleResource(ruleUuid)
        .then((response) => {
          this.editingRule = response.data.objects[0]
          this.ruleYamlTextArea = this.editingRule.rule_yaml // eslint-disable-line camelcase
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
          this.parseSigma(this.ruleYamlTextArea)
        })
    },
    deleteRule(ruleUuid) {
      if (confirm('Delete Rule?')) {
        ApiClient.deleteSigmaRule(ruleUuid)
          .then((response) => {
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
        ApiClient.createSigmaRule(this.ruleYamlTextArea)
          .then((response) => {
            this.$store.dispatch('updateSigmaList')
            EventBus.$emit('errorSnackBar', 'Rule created: ' + this.editingRule.id)
          })
          .catch((e) => {
            console.error(e)
          })
      }
      if (this.isUpdatingRule) {
        ApiClient.updateSigmaRule(this.editingRule.id, this.ruleYamlTextArea)
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
.editSigmaRule {
  font-family: monospace;
  font-size: 13px;
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