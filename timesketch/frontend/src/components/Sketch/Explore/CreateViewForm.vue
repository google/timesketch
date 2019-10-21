<!--
Copyright 2019 Google Inc. All rights reserved.

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
  <form v-on:submit.prevent="submitForm">
    <div class="field">
      <label class="label">Name</label>
      <div class="control">
        <input v-model="viewName" class="input" type="text" required placeholder="Name your view" autofocus>
      </div>
    </div>
    <div class="field">
      <div class="control">
        <input class="button is-success" type="submit" value="Save" v-on:click="toggleCreateViewModal">
      </div>
    </div>
  </form>
</template>

<script>
import ApiClient from '../../../utils/RestApiClient'

export default {
  name: 'ts-home-sketch-create-form',
  props: [
    'sketchId',
    'currentQueryString',
    'currentQueryFilter'
  ],
  data () {
    return {
      viewName: ''
    }
  },
  methods: {
    clearFormData: function () {
      this.viewName = ''
    },
    submitForm: function () {
      ApiClient.createView(this.sketchId, this.viewName, this.currentQueryString, this.currentQueryFilter).then((response) => {
        let newView = response.data.objects[0]
        this.$store.state.meta.views.push(newView)
        this.clearFormData()
        this.$router.push({ name: 'SearchPage', query: { view: newView.id } })
      }).catch((e) => {})
    },
    toggleCreateViewModal: function () {
      this.$emit('toggleCreateViewModal')
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
