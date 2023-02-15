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
  <div v-if="ruleCount > 0">
    <v-row
      no-gutters
      style="cursor: pointer"
      class="pa-4"
      flat
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <v-col cols="11">
        <v-icon left>mdi-sigma-lower</v-icon> Sigma Rules (<small
          ><strong>{{ ruleCount }}</strong></small
        >)
      </v-col>
      <v-col cols="1">
        <v-btn small icon>
          <v-icon v-if="expanded" v-on:click="createNewSigmaRule()">mdi-plus</v-icon>
        </v-btn>
      </v-col>
    </v-row>

    <v-expand-transition>
      <div v-show="expanded">
        <v-data-iterator :items="sigmaRules" :items-per-page.sync="itemsPerPage" :search="search">
          <template v-slot:header>
            <v-toolbar flat v-if="ruleCount > itemsPerPage">
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
  props: {
    startExpanded: Boolean,
  },
  components: {
    TsSigmaRule,
  },
  data: function () {
    return {
      expanded: this.startExpanded,
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

<style scoped lang="scss">
.v-text-field ::v-deep input {
  font-size: 0.9em;
}

.v-text-field ::v-deep label {
  font-size: 0.9em;
}
</style>
