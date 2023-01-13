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
    <!-- Left panel -->
    <v-navigation-drawer app permanent :width="navigationDrawer.width" hide-overlay ref="drawer">
      <v-toolbar flat color="transparent">
        <v-avatar class="ml-n1">
          <router-link to="/">
            <v-img src="/dist/timesketch-color.png" max-height="25" max-width="25" contain></v-img>
          </router-link> </v-avatar
        ><span style="font-size: 1.2em">Studio</span>
        <v-spacer></v-spacer>
      </v-toolbar>
      <v-divider></v-divider>
      <ts-sigma-rules></ts-sigma-rules>
    </v-navigation-drawer>
    <ts-sigma-rule-modification app @cancel="formatXMLString = false" :rule_uuid="id" v-if="type === 'sigma'">
    </ts-sigma-rule-modification>
    <ts-search-template-modification app :id="id" v-if="type === 'searchtemplate'"> </ts-search-template-modification>
  </div>
</template>

<script>
import TsSigmaRules from '../components/LeftPanel/SigmaRules'
import TsSigmaRuleModification from '../components/Studio/SigmaRuleModification.vue'
export default {
  props: ['showLeftPanel', 'id', 'type'],
  components: {
    TsSigmaRules,
    TsSigmaRuleModification,
  },
  data() {
    return {
      showSketchMetadata: false,
      navigationDrawer: {
        width: 450,
      },
    }
  },
  created: function () {
    this.$store.dispatch('updateSigmaList')
    document.title = 'Timesketch Studio'
  },

  computed: {
    meta() {
      return this.$store.state.meta
    },
  },
  watch: {
    showLeftPanel: function (newVal) {
      if (newVal === true) {
        this.navigationDrawer.width = 450
      }
    },
  },
}
</script>