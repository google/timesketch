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
            <h1>{{ editingRule.title }}</h1>
            <v-chip rounded x-small class="mr-2"
                :color="parsingStatusColors(problemString)">
                {{ problemString }}</v-chip>

            <v-alert colored-border border="left" elevation="1"
                :color="parsingStatusColors(problemString)">
                {{ problemString }}
            </v-alert>
            <div width="500">
                <b>Search Query:</b>
                <pre>{{ editingRule.search_query }}</pre>
            </div>
            <v-textarea label="Edit Sigma rule" outlined
                :color="parsingStatusColors('foo')" rows="35"
                v-model="rule_yaml" @input="parseSigma(rule_yaml)">
            </v-textarea>
            <div class="mt-3">
                <v-btn :disabled="problemString.toLowerCase() !== 'ok'"
                    @click="addOrUpdateRule(rule_yaml)" small depressed
                    color="primary">{{ save_button_text }}</v-btn>
                <v-btn @click="search(sigmaRule.search_query)" small depressed
                    color="secondary">Copy and tweak rule</v-btn>
                <v-btn @click="search(sigmaRule.search_query)" small depressed
                    color="secondary">Cancel</v-btn>
                <v-btn @click="deleteRule(rule_uuid)" small depressed
                    color="secondary">Delete Rule</v-btn>
            </div>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn text color="primary" @click="clearAndCancel"> Close
                </v-btn>
            </v-card-actions>
        </v-container>
    </v-card>
</template>
  
<script>
import { stringValue } from 'vega'
import ApiClient from '../../utils/RestApiClient'

export default {
    props: ['rule_uuid', 'sigmaRule'],
    data() {
        return {
            editingRule: { "rule_yaml": "foobar" },
            problemString: 'OK',
            save_button_text: "Update",
            rule_yaml: {},
        }
    },
    mounted() {
        this.getRuleByUUID(this.rule_uuid)
    },
    methods: {
        clearAndCancel: function () {
            this.$emit('cancel')
        },
        // Set debounce to 300ms if parseSigma is used.
        parseSigma: _.debounce(function (rule_yaml) { // eslint-disable-line
            this.problemString = ''
            ApiClient.getSigmaRuleByText(rule_yaml)
                .then(response => {
                    console.log(response.data.objects[0])
                    this.editingRule = response.data.objects[0]
                    this.problemString = 'OK'
                })
                .catch(e => {
                    this.problemString = 'PROBLEM please see console'
                    //console.log(e.response.data.message)
                    //this.problemString = e.response.data.message
                    // need to set search_query to something, to overwrite previous value
                    this.editingRule['search_query'] = 'PLEASE ADJUST RULE'
                })
        }, 300),
        parsingStatusColors(datasource) {
            if (this.problemString === 'OK') {
                return 'success'
            }
            return 'warning'
        },
        getRuleByUUID(ruleUuid) {
            console.log("getRuleByUUID" + ruleUuid)
            ApiClient.getSigmaRuleResource(ruleUuid = ruleUuid)
                .then(response => {
                    this.editingRule = response.data.objects[0]
                    this.rule_yaml = this.editingRule.rule_yaml
                    console.log("Found the rule + " + this.editingRule)
                    this.problemString = 'OK'
                })
                .catch(e => {
                    console.error(e)
                    this.save_button_text = "Create"
                })
            // TODO: show something if the rule uuid does not exist.
        },
        deleteRule(rule_uuid) {
            if (confirm('Delete Rule?')) {
                ApiClient.deleteSigmaRule(rule_uuid)
                    .then(response => {
                        console.log("Rule deleted: " + rule_uuid)
                        // remove element from Array
                        //this.$store.state.sigmaRuleList = this.sigmaRuleList.filter(obj => {
                        //    return obj.rule_uuid !== ioc.rule_uuid
                        //})
                    })
                    .catch(e => {
                        console.error(e)
                    })
            }
        },
        addOrUpdateRule: function (event) {
            if (this.save_button_text === "Create") {
                ApiClient.createSigmaRule(this.rule_yaml).then(response => {
                    this.$buefy.notification.open({
                        message: 'Succesfully added Sigma rule!',
                        type: 'is-success'
                    })
                    this.showEditModal = false
                    this.sigmaRuleList.push(response.data.objects[0])
                })
                    .catch(e => {
                        this.problemString = "Problem, please see console"
                        Snackbar.open({
                            message: this.problemString,
                            type: 'is-danger',
                            position: 'is-top',
                            indefinite: false,
                        })
                    })
            }
            if (this.save_button_text === "Update") {
                ApiClient.updateSigmaRule(this.editingRule.id, this.rule_yaml)
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