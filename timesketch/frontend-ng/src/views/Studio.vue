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
    <v-navigation-drawer app permanent width="450" hide-overlay ref="drawer">
      <v-toolbar flat color="transparent">
        <v-avatar class="ml-n1">
          <router-link to="/">
            <v-img src="/dist/timesketch-color.png" max-height="25" max-width="25" contain></v-img>
          </router-link> </v-avatar
        ><span style="font-size: 1.1em">Studio</span>
        <v-spacer></v-spacer>
      </v-toolbar>
      <v-divider></v-divider>
      <ts-sigma-rules></ts-sigma-rules>
    </v-navigation-drawer>

    <v-toolbar flat color="transparent">
      <v-spacer></v-spacer>
      <v-avatar color="grey lighten-1" size="25" class="ml-3">
        <span class="white--text">{{ currentUser | initialLetter }}</span>
      </v-avatar>
      <v-menu offset-y>
        <template v-slot:activator="{ on, attrs }">
          <v-avatar>
            <v-btn small icon v-bind="attrs" v-on="on">
              <v-icon>mdi-dots-vertical</v-icon>
            </v-btn>
          </v-avatar>
        </template>
        <v-card>
          <v-list>
            <v-list-item-group color="primary">
              <v-list-item v-on:click="toggleTheme">
                <v-list-item-icon>
                  <v-icon>mdi-brightness-6</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>Toggle theme</v-list-item-title>
                </v-list-item-content>
              </v-list-item>

              <a href="/logout/" style="text-decoration: none; color: inherit">
                <v-list-item>
                  <v-list-item-icon>
                    <v-icon>mdi-logout</v-icon>
                  </v-list-item-icon>

                  <v-list-item-content>
                    <v-list-item-title>Logout</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </a>
            </v-list-item-group>
          </v-list>
        </v-card>
      </v-menu>
    </v-toolbar>
    <!-- Middle panel -->
    <ts-sigma-rule-modification app @cancel="formatXMLString = false" :rule_uuid="id" v-if="type === 'sigma'">
    </ts-sigma-rule-modification>
  </div>
</template>

<script>
import TsSigmaRules from '../components/LeftPanel/SigmaRules'
import TsSigmaRuleModification from '../components/Studio/SigmaRuleModification.vue'
export default {
  props: ['id', 'type'],
  components: {
    TsSigmaRules,
    TsSigmaRuleModification,
  },
  methods: {
    toggleTheme() {
      this.$vuetify.theme.dark = !this.$vuetify.theme.dark
    },
  },
  computed: {
    currentUser() {
      return this.$store.state.currentUser
    },
  },
  created: function () {
    this.$store.dispatch('updateSigmaList')
    document.title = 'Timesketch Studio'
  },
}
</script>