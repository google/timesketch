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
    <strong>{{ rule.id }}</strong>
    <ul class="content-list">
      <li v-for="(value, name) in rule" v-bind:key="name" style="padding:10px;border-bottom:none;cursor:pointer;">
        <div>
          <b>{{ name }}</b
          >: <code>{{ value }}</code>
        </div>
      </li>
    </ul>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  data() {
    return {
      rule: [],
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
