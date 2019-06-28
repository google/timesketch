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
  <div class="field is-horizontal" v-if="schema.length">
    <div class="field-body">

      <component v-for="(field, index) in schema"
                 :key="index"
                 :is="field.type"
                 :value="formData[field.name]"
                 @input="updateForm(field.name, $event)"
                 v-bind="field">
      </component>

      <p class="control">
        <input class="button is-success" type="submit" value="Run">
      </p>
    </div>
  </div>
  </form>
</template>

<script>
import TsDynamicFormTextInput from './DynamicFormTextInput'
import TsDynamicFormRadioInput from './DynamicFormRadioInput'

export default {
  name: 'ts-dynamic-form',
  props: ['schema', 'value'],
  components: { TsDynamicFormTextInput, TsDynamicFormRadioInput },
  data () {
    return {
      formData: this.value || {}
    }
  },
  methods: {
    updateForm (fieldName, value) {
      this.$set(this.formData, fieldName, value)
      this.$emit('input', this.formData)
    },
    submitForm () {
      this.$emit('formSubmitted')
    }
  }
}
</script>

<style lang="scss"></style>
