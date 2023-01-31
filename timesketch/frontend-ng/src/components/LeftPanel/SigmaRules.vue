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
    <div class="pa-4" flat :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
      <span style="cursor: pointer" @click="expanded = !expanded">
        <v-icon left>mdi-sigma-lower</v-icon> Sigma Rules ({{ ruleCount }})
      </span>
      <span style="float: right" v-if="expanded">
        <v-icon v-on:click="createNewSigmaRule()">mdi-plus</v-icon>
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded" v-if="ruleCount > 0">
        <v-data-iterator :items="sigmaRules" :items-per-page.sync="itemsPerPage" :search="search">
          <template v-slot:header>
            <v-toolbar flat>
              <v-text-field
                v-model="search"
                clearable
                hide-details
                outlined
                dense
                prepend-inner-icon="mdi-magnify"
                label="Search for a rule.."
              ></v-text-field>
            </v-toolbar>
          </template>

          <template v-slot:default="props">
            <ts-sigma-rule v-for="sigmaRule in props.items" :key="sigmaRule.rule_uuid" :sigma-rule="sigmaRule">
            </ts-sigma-rule>
          </template>
        </v-data-iterator>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import TsSigmaRule from './SigmaRule.vue'

export default {
  props: [],
  components: {
    TsSigmaRule,
  },
  data: function () {
    return {
      expanded: false,
      itemsPerPage: 10,
      search: '',
    }
  },
  methods: {
    createNewSigmaRule() {
      // check current router location
      if (this.$route.params.id === 'new') {
        return
      }
      this.$router.push({
        name: 'Studio',
        params: {
          id: 'new',
          type: 'sigma',
        },
      })
    },
  },
  computed: {
    sigmaRules() {
      return this.$store.state.sigmaRuleList
    },
    ruleCount() {
      // to avoid undefined error if the list is not yet loaded or number is 0
      if (!this.$store.state.sigmaRuleList) {
        return 0
      }
      return this.$store.state.sigmaRuleList.length
    },
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  created() {
    this.$store.dispatch('updateSigmaList')
  },
}
</script>