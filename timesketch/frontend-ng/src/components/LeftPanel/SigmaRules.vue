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
    <div class="pa-4" flat
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
      <span style="cursor: pointer" @click="expanded = !expanded">
        <v-icon left>mdi-sigma-lower</v-icon> Sigma Rules ({{ sigmaRules.length
        }}) <v-btn @click="CreateNewRule()" small depressed color="green">
          Create Rule</v-btn>
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded">
        <v-data-iterator :items="sigmaRules" :items-per-page.sync="itemsPerPage"
          :search="search">

          <template v-slot:header>
            <v-toolbar flat>
              <v-text-field v-model="search" clearable hide-details outlined
                dense prepend-inner-icon="mdi-magnify"
                label="Search for a rule.."></v-text-field>
            </v-toolbar>
          </template>

          <template v-slot:default="props">
            <ts-sigma-rule v-for="sigmaRule in props.items"
              :key="sigmaRule.rule_uuid" :sigma-rule="sigmaRule">
            </ts-sigma-rule>
          </template>
        </v-data-iterator>
      </div>
      <div>
        <pre>{{ sigmaRules | pretty }}</pre>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsSigmaRule from './SigmaRule.vue'

export default {
  props: [],
  components: {
    TsSigmaRule,
  },
  data: function () {
    return {
      sigmaRules: [],
      expanded: false,
      itemsPerPage: 10,
      search: '',
    }
  },
  methods: {
    CreateNewRule(){
      //this.$store.dispatch('updateSearchNode', this.selectedNode)
      this.$router.push('/studio/sigma/'+crypto.randomUUID()); 
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  created() {
    ApiClient.getSigmaRuleList()
      .then((response) => {
        this.sigmaRules = response.data.objects
      })
      .catch((e) => { })
  },
}
</script>