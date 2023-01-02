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
  <v-card width="1000" style="overflow: initial">
    <v-container class="px-8">
      <h1>
        Rule title: {{ editingRule.title }}
        <v-chip rounded x-small class="mr-2" :color="statusColors(status_chip_text)">
          <v-icon v-if="status_text.toLowerCase() !== 'ok'"> mdi-alert </v-icon>
          <v-icon v-if="status_text.toLowerCase() === 'ok'"> mdi-check </v-icon>
          {{ status_chip_text }}</v-chip
        >
      </h1>

      <div>
        <v-autocomplete dense filled rounded :items="SigmaTemplates" @change="rowClick" item-text="title">
        </v-autocomplete>
      </div>
      <div width="500" v-if="status_text.toLowerCase() !== 'ok'">
        <!-- only display if status_text is not empty -->
        <v-alert dense type="warning">
          {{ status_text }}
        </v-alert>
      </div>

      <v-textarea
        label="Edit Sigma rule"
        outlined
        :color="statusColors(status_chip_text)"
        autocomplete="email"
        rows="25"
        v-model="ruleYaml"
        background-color="lighten(statusColors(status_chip_text), 0.2)"
        @input="parseSigma(ruleYaml)"
      >
      </v-textarea>

      <div width="500" v-if="status_text.toLowerCase() === 'ok'">
        <v-alert colored-border border="left" elevation="1" :color="statusColors(status_chip_text)">
          <b>Search Query:</b>
          {{ editingRule.search_query }}
        </v-alert>
      </div>

      <div class="mt-3">
        <v-btn
          :disabled="status_chip_text.toLowerCase() !== 'ok'"
          @click="addOrUpdateRule(ruleYaml)"
          small
          depressed
          color="primary"
          >{{ action_button_text }}</v-btn
        >
        <div style="width: 20px; display: inline-block"></div>
        <v-btn @click="cancel" small depressed color="secondary">Cancel </v-btn>
        <!-- make 20 px space° -->
        <div style="width: 20px; display: inline-block"></div>
        <v-btn
          @click="deleteRule(rule_uuid)"
          small
          depressed
          color="red"
          :disabled="action_button_text.toLowerCase() == 'create'"
          >Delete Rule</v-btn
        >
      </div>
    </v-container>
  </v-card>
</template>
  
<script>
import ApiClient from '../../utils/RestApiClient'
import { SigmaTemplates, GeneralText } from '@/utils/SigmaRuleTemplates'
import EventBus from '../../main'
import _ from 'lodash'

export default {
  props: ['rule_uuid', 'sigmaRule'],
  data() {
    return {
      editingRule: { ruleYaml: 'foobar' }, // empty state
      status_chip_text: 'OK',
      status_text: 'OK',
      action_button_text: 'Update Rule',
      ruleYaml: {},
      SigmaTemplates: SigmaTemplates,
      search: '',
    }
  },
  watch: {
    rule_uuid: function (newVal, oldVal) {
      this.getRuleByUUID(newVal)
    },
  },
  mounted() {
    // check if router was called with sigma/new
    if (this.rule_uuid === 'new') {
      this.editingRule = {
        title: 'New Sigma Rule',
      }
      this.action_button_text = 'Create Rule'
      this.status_chip_text = 'OK'
    }
    // even if the rule was stored, we want to double check the rule

    this.getRuleByUUID(this.rule_uuid)
  },
  methods: {
    cancel() {
      this.$router.back()
    },

    rowClick(text) {
      var matchingTemplate = this.SigmaTemplates.find((obj) => {
        return obj.title === text
      })
      this.ruleYaml = matchingTemplate.text
      this.parseSigma(matchingTemplate.text)
    },
    // Set debounce to 300ms if parseSigma is used.
    parseSigma: _.debounce(function (ruleYaml) {
      // eslint-disable-line
      ApiClient.getSigmaRuleByText(ruleYaml)
        .then((response) => {
          var parsedRule = response.data.objects[0]
          if (!parsedRule.author) {
            this.status_text = 'No Author given'
          } else {
            this.editingRule = parsedRule
            this.status_chip_text = 'Ok'
            this.status_text = 'Ok'
          }
        })
        .catch((e) => {
          // this.editingRule['search_query'] = e.response.data.message
          this.status_text = e.response.data.message
          // need to set search_query to something, to overwrite previous value
          this.status_chip_text = 'ERROR'
        })
    }, 300),
    statusColors() {
      if (this.status_chip_text.toLowerCase() === 'ok' || this.status_text.toLowerCase() === 'ok') {
        return 'success'
      }
      return 'warning'
    },
    getRuleByUUID(ruleUuid) {
      ApiClient.getSigmaRuleResource(ruleUuid)
        .then((response) => {
          this.editingRule = response.data.objects[0]
          this.ruleYaml = this.editingRule.rule_yaml // eslint-disable-line camelcase
          this.status_chip_text = 'Ok'
        })
        .catch((e) => {
          console.error(e)
          this.action_button_text = 'Create Rule'
          this.status_chip_text = 'Ok'
          this.ruleYaml = GeneralText
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
      if (this.status_chip_text !== 'Ok') {
        // There seems still a parsing error, do not store them
        console.error('Sigma parsing still has error, please fix')
      } else if (this.status_chip_text === 'Ok') {
        if (this.action_button_text.includes('Create')) {
          ApiClient.createSigmaRule(this.ruleYaml)
            .then((response) => {
              this.$store.dispatch('updateSigmaList')
              EventBus.$emit('errorSnackBar', 'Rule created: ' + this.editingRule.id)
            })
            .catch((e) => {
              this.editingRule['search_query'] = e.response.data.message // need to set search_query to something, to overwrite previous value
            })
        }
        if (this.action_button_text.includes('Update')) {
          ApiClient.updateSigmaRule(this.editingRule.id, this.ruleYaml)
            .then((response) => {
              this.$store.dispatch('updateSigmaList')
              EventBus.$emit('errorSnackBar', 'Rule updated: ' + this.editingRule.id)
            })
            .catch((e) => {})
        }
      }
    },
  },
}
</script>
  
<style scoped lang="scss">
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