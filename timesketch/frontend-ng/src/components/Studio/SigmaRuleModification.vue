<!--
Copyright 2022 Google Inc. All rights reserved.

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
        <v-chip rounded x-small class="mr-2" :color="parsingStatusColors(ok_button_text)"> {{ ok_button_text }}</v-chip>
      </h1>

      <div>
        <v-autocomplete dense filled rounded :items="SigmaTemplates" @change="rowClick" item-text="title">
        </v-autocomplete>
      </div>

      <div width="500">
        <v-alert colored-border border="left" elevation="1" :color="parsingStatusColors(ok_button_text)">
          <b>Search Query:</b>
          {{ editingRule.search_query }}
        </v-alert>
      </div>

      <v-textarea
        label="Edit Sigma rule"
        outlined
        :color="parsingStatusColors('foo')"
        rows="35"
        v-model="ruleYaml"
        @input="parseSigma(ruleYaml)"
      >
      </v-textarea>
      <div class="mt-3">
        <v-btn
          :disabled="ok_button_text.toLowerCase() !== 'ok'"
          @click="addOrUpdateRule(ruleYaml)"
          small
          depressed
          color="primary"
          >{{ save_button_text }}</v-btn
        >
        <v-btn @click="cancel" small depressed color="secondary">Cancel </v-btn>
        <v-btn
          @click="deleteRule(rule_uuid)"
          small
          depressed
          color="red"
          :disabled="save_button_text.toLowerCase() == 'create'"
          >Delete Rule</v-btn
        >
      </div>

      <!-- TODO: Remove before merging -->
      <div>
        <pre>
                {{ editingRule }}
            </pre
        >
      </div>
    </v-container>
  </v-card>
</template>
  
<script>
import ApiClient from '../../utils/RestApiClient'
import { SigmaTemplates } from '@/utils/SigmaRuleTemplates'
import EventBus from '../../main'

export default {
  props: ['rule_uuid', 'sigmaRule'],
  data() {
    return {
      editingRule: { ruleYaml: 'foobar' }, // empty state
      ok_button_text: 'OK',
      save_button_text: 'Update',
      ruleYaml: {},
      SigmaTemplates: SigmaTemplates,
      search: '',
    }
  },

  mounted() {
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
          console.log(response.data.objects[0])
          if (!response.data.objects[0].author) {
            this.search_query = 'No Author given'
          } else {
            this.editingRule = response.data.objects[0]
            this.ok_button_text = 'OK'
          }
        })
        .catch((e) => {
          this.editingRule['search_query'] = e.response.data.message
          // need to set search_query to something, to overwrite previous value
          this.ok_button_text = 'ERROR'
        })
    }, 300),
    parsingStatusColors(datasource) {
      if (this.ok_button_text === 'OK') {
        return 'success'
      }
      return 'warning'
    },
    getRuleByUUID(ruleUuid) {
      ApiClient.getSigmaRuleResource((ruleUuid = ruleUuid))
        .then((response) => {
          this.editingRule = response.data.objects[0]
          this.ruleYaml = this.editingRule.rule_yaml // eslint-disable-line camelcase
          this.ok_button_text = 'OK'
        })
        .catch((e) => {
          console.error(e)
          this.save_button_text = 'Create'
          this.ok_button_text = 'Ok'
          this.editingRule['search_query'] = 'No Rule found, creating a new one'
          this.ruleYaml = `title: Foobar
id: ${crypto.randomUUID()}
description: Detects suspicious FOOBAR
references:
  - https://
author: ${this.$store.state.currentUser}
date: ${new Date(Date.now()).toLocaleString('en-ZA').split(',')[0]}
modified: ${new Date(Date.now()).toLocaleString('en-ZA').split(',')[0]}
status: experimental
falsepositives: unknown
level: informational
tags:
    -`
        })
    },
    deleteRule(rule_uuid) {
      if (confirm('Delete Rule?')) {
        ApiClient.deleteSigmaRule(rule_uuid)
          .then((response) => {
            console.log('Rule deleted: ' + rule_uuid)
            this.$store.dispatch('updateSigmaList')
            EventBus.$emit('errorSnackBar', 'Rule deleted: ' + rule_uuid)
          })
          .catch((e) => {
            console.error(e)
          })
      }
    },
    addOrUpdateRule: function (event) {
      if (this.ok_button_text !== 'OK') {
        // There seems still a parsing error, do not store them
        console.error('Sigma parsing still has error, please fix')
      } else if (this.ok_button_text === 'OK') {
        if (this.save_button_text === 'Create') {
          ApiClient.createSigmaRule(this.ruleYaml)
            .then((response) => {
              // todo(jaegeral): make a nicer feedback to the user
              EventBus.$emit('errorSnackBar', 'Rule created: ' + rule_uuid)
              this.sigmaRuleList.push(response.data.objects[0])
              this.$store.dispatch('updateSigmaList')
            })
            .catch((e) => {
              this.editingRule['search_query'] = e.response.data.message // need to set search_query to something, to overwrite previous value
            })
        }
        if (this.save_button_text === 'Update') {
          ApiClient.updateSigmaRule(this.editingRule.id, this.ruleYaml)
            .then((response) => {
              this.$store.state.sigmaRuleList = this.sigmaRuleList.filter((obj) => {
                return obj.rule_uuid !== this.editingRule.rule_uuid
              })
              this.sigmaRuleList.push(response.data.objects[0])
              EventBus.$emit('errorSnackBar', 'Rule updated: ' + rule_uuid)
            })
            .catch((e) => {})
        }
        this.$store.dispatch('updateSigmaList')
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