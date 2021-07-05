<!--
Copyright 2021 Google Inc. All rights reserved.

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
    <table class="table is-fullwidth">
      <tr>
        <th>Key</th>
        <th>Value</th>
      </tr>
      <tr v-for="(value, name) in rule" v-bind:key="name">
        <td>
          {{ name }}
        </td>
        <td @mouseover="c_name = name" @mouseleave="c_name = -1">
          <div v-if="name === 'tags'">
            <ul class="content-list">
              <li style="padding:10px;border-bottom:none;cursor:pointer;">
                <div v-for="tag in value" v-bind:key="tag">
                  {{ tag }}
                  <span class="icon is-small" v-if="name == c_name">
                    <router-link :to="{ name: 'Explore', query: { q: tag } }"><i class="fas fa-search"></i></router-link
                  ></span>
                </div>
              </li>
            </ul>
          </div>
          <div v-else-if="name === 'es_query'">
            <code>{{ value }}</code>
            <span class="icon is-small" v-if="name == c_name">
              <router-link :to="{ name: 'Explore', query: { q: value } }"><i class="fas fa-search"></i></router-link
            ></span>
            <i
              class="fas fa-copy"
              v-if="name == c_name"
              style="cursor:pointer;float:right;"
              title="Copy key:value"
              v-clipboard:copy="value"
              v-clipboard:success="handleCopyStatus"
            ></i>
          </div>
          <div v-else>
            <code>{{ value }}</code>
            <i
              class="fas fa-copy"
              v-if="name == c_name"
              style="cursor:pointer;float:right;"
              title="Copy key:value"
              v-clipboard:copy="value"
              v-clipboard:success="handleCopyStatus"
            ></i>
          </div>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  data() {
    return {
      rule: [],
      c_name: -1,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    ruleId() {
      return this.$route.query.ruleId
    },
    meta() {
      return this.$store.state.meta
    },
    handleCopyStatus: function() {
      this.$buefy.notification.open('Copied!')
    },
  },
  created() {
    // TODO (jaegeral): change that to use the rule from the already stored one
    //this.asd = this.$store.state.sigmaRuleList.find(rule => rule.ruleId === this.$route.query.ruleId)

    ApiClient.getSigmaResource(this.$route.query.ruleId)
      .then(response => {
        this.rule = response.data['objects'][0]
      })
      .catch(e => {
        console.error(e)
      })
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
