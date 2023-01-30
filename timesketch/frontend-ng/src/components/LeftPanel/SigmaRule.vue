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
  <div>
    <v-row no-gutters class="pa-2" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
      <div @click="expanded = !expanded" style="cursor: pointer; font-size: 0.9em">
        <v-icon v-if="!expanded">mdi-chevron-right</v-icon>
        <v-icon v-else>mdi-chevron-down</v-icon>
        {{ sigmaRule.title }}<v-chip rounded x-small class="ml-2">{{ sigmaRule.status }}</v-chip>
      </div>
      <v-spacer></v-spacer>
      <div>
        <v-menu>
          <template v-slot:activator="{ on, attrs }">
            <v-btn small icon v-bind="attrs" v-on="on">
              <v-icon>mdi-dots-vertical</v-icon>
            </v-btn>
          </template>
          <v-card>
            <v-list>
              <v-list-item-group>
                <v-list-item v-on:click="editSigmaRule(sigmaRule.rule_uuid)">
                  <v-list-item-icon>
                    <v-icon>mdi-pencil </v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>Edit Rule</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
                <v-list-item v-on:click="deprecateSigmaRule(sigmaRule.rule_uuid)">
                  <v-list-item-icon>
                    <v-icon>mdi-archive</v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>Do not use the rule in Sigma analyzer</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
                <v-list-item v-on:click="deleteRule(sigmaRule.rule_uuid)">
                  <v-list-item-icon>
                    <v-icon>mdi-delete</v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>Delete Rule</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </v-list-item-group>
            </v-list>
          </v-card>
        </v-menu>
      </div>
    </v-row>

    <v-expand-transition>
      <div v-show="expanded" class="pa-4 pt-0">
        <!--{{ sigmaRuleSummary }}-->
        <div class="mt-2">
          <v-simple-table dense>
            <template v-slot:default>
              <tbody>
                <tr v-for="(value, key) in sigmaRuleSummary" :key="value.rule_uuid">
                  <td>
                    <strong>{{ key }}</strong>
                  </td>
                  <td>
                    <span v-if="key === 'references'">
                      <div v-for="ref in value" :key="ref">
                        <a :href="ref" target="new">{{ ref }}</a>
                      </div>
                    </span>
                    <span v-else-if="key === 'falsepositives'">
                      <v-chip v-for="falsepositive in value" :key="falsepositive" rounded x-small class="mr-2">{{
                        falsepositive
                      }}</v-chip>
                    </span>

                    <span v-else-if="key === 'tags'">
                      <v-chip v-for="tag in value" :key="tag" rounded x-small class="mr-2">{{ tag }}</v-chip>
                    </span>
                    <span v-else>
                      {{ value }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </template>
          </v-simple-table>
        </div>

        <div class="mt-3">
          <v-btn @click="search(sigmaRule.search_query)" small depressed color="primary" v-if="sketch.id !== undefined"
            >Search</v-btn
          >
        </div>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import EventBus from '../../main'
import ApiClient from '../../utils/RestApiClient'

const defaultQueryFilter = () => {
  return {
    from: 0,
    terminate_after: 40,
    size: 40,
    indices: '_all',
    order: 'asc',
    chips: [],
  }
}

export default {
  components: {},
  props: ['sigmaRule'],
  data: function () {
    return {
      expanded: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    sigmaRuleSummary() {
      const fields = [
        'author',
        'description',
        'references',
        'status',
        'date',
        'modified',
        'falsepositives',
        'level',
        'tags',
        'rule_uuid',
        'search_query',
      ]
      return Object.fromEntries(Object.entries(this.sigmaRule).filter(([key]) => fields.includes(key)))
    },
  },
  methods: {
    search(queryString) {
      // if sketch.id is undefined, we are in the sigma list view and not searching
      if (!this.sketch.id) {
        return
      }
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = queryString
      eventData.queryFilter = defaultQueryFilter()
      console.log(eventData)
      EventBus.$emit('setQueryAndFilter', eventData)
    },
    editSigmaRule(ruleUuid) {
      console.log('Edit Rule: ' + ruleUuid)
      this.$router.push({
        name: 'Studio',
        params: {
          id: ruleUuid,
          type: 'sigma',
        },
      })
    },
    deleteRule(ruleUuid) {
      if (confirm('Delete Rule?')) {
        ApiClient.deleteSigmaRule(ruleUuid)
          .then((response) => {
            console.log('Rule deleted: ' + ruleUuid)
            this.$store.dispatch('updateSigmaList')
            this.$router.push({
              name: 'Studio',
              params: {
                id: 'new',
                type: 'sigma',
              },
            })
          })
          .catch((e) => {
            console.error(e)
          })
      }
    },
    deprecateSigmaRule(ruleUuid) {
      // this method is not really deprecating the rule, but for lack of better
      // words, it is changing the status to deprecated. This means the rule
      // will not be picked up by the Sigma analyzer.
      if (confirm('Deprecate Rule?')) {
        //  get the current Sigma rule yaml again
        ApiClient.getSigmaRuleResource(ruleUuid)
          .then((response) => {
            var editingRule = response.data.objects[0]
            const regex = /status:\s*(experimental|testing|stable)/g
            var ruleYaml = editingRule.rule_yaml.replace(regex, 'status: deprecated')
            ApiClient.updateSigmaRule(ruleUuid, ruleYaml)
              .then(() => {
                console.log('Rule deprecated: ' + ruleUuid)
                this.$store.dispatch('updateSigmaList')
                EventBus.$emit('errorSnackBar', 'Rule deprecated: ' + ruleUuid)
              })
              .catch((e) => {
                console.error(e)
              })
          })
          .catch((e) => {
            console.error(e)
          })
      }
    },
  },
}
</script>

<style scoped lang="scss">
.SigmaRuleTitle {
  cursor: pointer;
  font-size: 0.9em;
}
</style>