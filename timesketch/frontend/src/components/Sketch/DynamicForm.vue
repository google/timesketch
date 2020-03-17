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
  <form v-if="schema.length" v-on:submit.prevent="submitForm">
      <component v-for="(field, index) in schema"
                 :key="index"
                 :is="field.type"
                 :value="formData[field.name]"
                 :display="field.display"
                 @input="updateForm(field.name, $event)"
                 v-bind="field">
      </component>
      <div class="control">
        <input class="button is-info" type="submit" value="Run">
      </div>
  </form>
</template>

<script>
import TsDynamicFormTextInput from './DynamicFormTextInput'
import TsDynamicFormSelectInput from './DynamicFormSelectInput'

export default {
  components: { TsDynamicFormTextInput, TsDynamicFormSelectInput },
  props: ['schema', 'value'],
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
