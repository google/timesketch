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
      <ul class="content-list">
        <li style="padding:10px;border-bottom:none;cursor:pointer;">
          <strong style="color: var(--default-font-color)">{{ rule.id }}</strong>
          <br />
          {{ ruleId }}
          <div v-for="(value, name) in rule" v-bind:key="name">
            {{ name }}: {{ value }}
        </div>
        </li>
      </ul>

  <!-- jaegeral: This is draft currently -->
   <form v-on:submit.prevent="submitForm">
    <div class="field">
      <label class="label">Sigma Text</label>
      <div class="multiline">
        <input v-model="SigmaText" class="input" type="text" required placeholder="SigmaText" autofocus />
      </div>
    </div>
    <div class="field">
      <div class="control">
        <input class="button is-success" type="submit" value="Save" />
      </div>
    </div>
  </form>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  data() {
    return {
      rule: [],
      SigmaText : '',
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
    // TOTO (jaegeral): change that to use the rule from the already stored one
    ApiClient.getSigmaResource(this.$route.query.ruleId)
      .then(response => {
        this.rule = response.data['objects'][0]
        console.log(this.rule)
      })
      .catch(e => {
        console.error(e)
      })
  },
  methods: {
    clearFormData: function() {
      this.SigmaText = ''
    },
    submitForm: function() {
      ApiClient.getSigmaByText(this.SigmaText)
        .then(response => {
          let newView = response.data.objects[0]
          console.log(newView)
          //this.$emit('setActiveView', newView)
          //this.$store.state.meta.views.push(newView)
          //this.clearFormData()
          //this.$router.push({ name: 'Explore', query: { view: newView.id } })
        })
        .catch(e => {})
    },
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
