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
  <v-dialog :value="dialog" @input="$emit('input', $event)" max-width="600px" @click:outside="closeDialog()">
    <v-card class="pa-4">
      <h3>{{ title }}</h3>
      <br />
      <v-text-field outlined label="Indicator data" v-model="newIndicator.ioc" @input="autoSelectIndicatorType($event)">
      </v-text-field>
      <v-select outlined label="Indicator type" v-model="newIndicator.type" :items="indicatorTypes"> </v-select>
      <v-combobox
        v-model="newIndicator.tags"
        :items="Object.keys(this.tagInfo)"
        label="Add tags.. (optional)"
        outlined
        chips
        small-chips
        multiple
      ></v-combobox>
      <v-text-field outlined label="External reference (optional)" v-model="newIndicator.externalURI"> </v-text-field>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="closeDialog()"> Cancel </v-btn>
        <v-btn text color="primary" :disabled="!newIndicator.ioc" @click="saveIndicator"> Save </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { IOCTypes } from '@/utils/ThreatIntelMetadata'

const newIndicator = () => {
  return {
    ioc: '',
    type: 'other',
    externalURI: '',
    tags: [],
  }
}

export default {
  props: ['dialog', 'tagInfo', 'index'],
  data() {
    return {
      IOCTypes: IOCTypes,
      newIndicator: newIndicator(),
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    intelligenceAttribute() {
      if (this.meta.attributes.intelligence === undefined) {
        return { ontology: 'intelligence', value: { data: [] }, name: 'intelligence' }
      }
      return this.meta.attributes.intelligence
    },
    indicatorTypes() {
      return this.IOCTypes.map((IOCtype) => IOCtype.type)
    },
    title() {
      if (this.index < 0) {
        return 'Create new indicator'
      }
      return 'Edit indicator'
    },
  },
  methods: {
    closeDialog: function () {
      this.$emit('close-dialog')
    },
    autoSelectIndicatorType: function (value) {
      // Check input against known indicator types and suggest value for select.
      for (const IOCtype of this.IOCTypes) {
        if (IOCtype.regex.test(value)) {
          this.newIndicator.type = IOCtype.type
          return
        }
      }
    },
    saveIndicator: function () {
      this.$emit('save', this.newIndicator)
      this.newIndicator = newIndicator()
    },
  },
  watch: {
    index() {
      if (this.index < 0) {
        this.newIndicator = newIndicator()
      } else {
        this.newIndicator = this.intelligenceAttribute.value.data[this.index]
      }
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
