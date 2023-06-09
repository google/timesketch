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
    <div
      :style="!(sigmaRules && sigmaRules.length) ? '' : 'cursor: pointer'"
      class="pa-4"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span> <v-icon left>mdi-sigma-lower</v-icon> Sigma Rules </span>

      <v-btn
        v-if="expanded || (sigmaRules && !sigmaRules.length)"
        icon
        text
        class="float-right mt-n1 mr-n1"
        :to="{ name: 'SigmaNewRule', params: { sketchId: sketch.id } }"
        @click.stop=""
      >
        <v-icon>mdi-plus</v-icon>
      </v-btn>
      <span v-if="!expanded" class="float-right" style="margin-right: 3px">
        <v-progress-circular v-if="isLoading" :size="24" :width="1" indeterminate></v-progress-circular>
      </span>
      <span v-if="!expanded" class="float-right" style="margin-right: 10px">
        <small v-if="sigmaRules && sigmaRules.length"
          ><strong>{{ ruleCount }}</strong></small
        >
      </span>
    </div>

    <v-expand-transition>
      <div v-show="expanded">
        <div v-if="sigmaRules && sigmaRules.length">
          <v-data-iterator v-if="ruleCount <= itemsPerPage" :items="sigmaRules" hide-default-footer>
            <template v-slot:default="props">
              <ts-sigma-rule v-for="sigmaRule in props.items" :key="sigmaRule.rule_uuid" :sigma-rule="sigmaRule" />
            </template>
          </v-data-iterator>
          <v-data-iterator v-else :items="sigmaRules" :items-per-page.sync="itemsPerPage" :search="search">
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
              <ts-sigma-rule v-for="sigmaRule in props.items" :key="sigmaRule.rule_uuid" :sigma-rule="sigmaRule" />
            </template>
          </v-data-iterator>
        </div>
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
  methods: {},
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
    isLoading() {
      return !this.sigmaRules
    },
  },
  mounted() {
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
