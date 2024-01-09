<!--
 Copyright 2024 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 -->
<template>
  <v-container>
    <v-row v-for="(queryChip, index) in queryChips" :key="index">
      <v-col md="3">
        <v-text-field
          label="Type"
          outlined
          readonly
          :dense="isDense"
          v-model="queryChip.type"
        ></v-text-field>
      </v-col>
      <v-col md="3">
        <v-text-field
          label="Field"
          outlined
          readonly
          :dense="isDense"

          v-model="queryChip.field"
        ></v-text-field>
      </v-col>
      <v-col md="2">
        <v-select
          v-model="queryChip.operator"
          label="Operator"
          :items="clauseTypes"
          outlined
          readonly
          :dense="isDense"

        ></v-select>
      </v-col>
      <v-col md="3">
        <v-text-field
          label="Value"
          outlined
          readonly
          :dense="isDense"

          v-model="queryChip.value"
        ></v-text-field>
      </v-col>
      <v-col md="auto">
        <v-btn :class="isDense ? 'mt-1' : 'mt-3'"
          fab x-small color="primary"
          @click="queryChips.splice(index, 1)"
        >
          <v-icon>
            mdi-close
          </v-icon>
        </v-btn>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-btn @click="showAddChipRow = !showAddChipRow" v-if="!showAddChipRow">Add New Filter</v-btn>
      </v-col>
    </v-row>
    <v-row v-if="showAddChipRow">
      <v-col md="3">
        <v-select
          v-model="newFilterTermType"
          label="Type"
          :items="chipTypes"
          outlined
          :dense="isDense"
        ></v-select>
      </v-col>
      <v-col md="3">
        <v-select
          v-model="newFilterFieldName"
          label="Field"
          :items="fieldItems"
          outlined
          :dense="isDense"
          :disabled="newFilterTermType === 'datetime_range'"
        ></v-select>
      </v-col>
      <v-col md="2">
        <v-select
          v-model="newFilterClauseType"
          label="Operator"
          :items="clauseTypes"
          outlined
          :dense="isDense"
        ></v-select>
      </v-col>
      <v-col md="3">
        <v-text-field
          v-model="newFilterFieldValue"
          label="Value"
          hint="Enter the filter value"
          outlined
          :dense="isDense"
        ></v-text-field>
      </v-col>
      <v-col md="1">
        <v-btn
          :class="isDense ? 'mt-1' : 'mt-3'"
          fab x-small
          @click="addNewFilter"
        >
          <v-icon v-if="isNewTermFilterDisabled">
            mdi-window-close
          </v-icon>
          <v-icon v-if="!isNewTermFilterDisabled">
            mdi-plus
          </v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>

export default {
  components: {

  },
  props: {
    selectedQueryChips: { type: Array, default: function() { return [] }},
    isDense: { type: Boolean, default: false },
  },
  data() {
    return {
      chipTypes: ["label", "term", "datetime_range"],
      clauseTypes: ["must", "should", "must_not"],
      newFilterTermType: "term",
      newFilterClauseType: "must",
      newFilterFieldName: null,
      newFilterFieldValue: null,
      queryChips: this.selectedQueryChips,
      showAddChipRow: false,
    }
  },
  computed: {
    isNewTermFilterDisabled() {
      return !(
          this.newFilterTermType != null &&
          this.newFilterClauseType != null &&
          this.newFilterFieldName != null &&
          //this.newFilterFieldName != "" &&
          this.newFilterFieldValue != null &&
          this.newFilterFieldValue != ""
      ) // TODO: add more validation for datetime_range and
    },
    fieldItems() {
      if (this.newFilterTermType === 'label') {
        return [{ text:'label', value: 'label' }]
      } else if (this.newFilterTermType === 'term') {
        return this.allNonTimestampFields
      } else if (this.newFilterTermType === 'datetime_range') {
        return [{ text:'', value: '' }]
      } else {
        return []
      }
    },
    allNonTimestampFields() {
      let mappings = this.$store.state.meta.mappings
        .filter(
          (mapping) => {
            return (
              mapping['field'] !== 'datetime'
              && mapping['field'] !== 'timestamp'
            )
        })
        .map(
          (mapping) => {
            return {text: mapping['field'], value: mapping}}
        )
      return mappings
    },
  },
  methods: {
    addNewFilter() {
      if (this.isNewTermFilterDisabled) {
        this.showAddChipRow = false
        return
      }
      this.queryChips.push({
          type: this.newFilterTermType, operator: this.newFilterClauseType,
          field: this.newFilterFieldName.field, value: this.newFilterFieldValue
      });
      this.newFilterTermType = this.chipTypes[0];
      this.newFilterClauseType = this.clauseTypes[0];
      if (this.fieldItems.length > 0) {
        this.newFilterFieldName = this.fieldItems[0];
      } else {
        this.newFilterFieldName = undefined
      }
      this.newFilterFieldValue = undefined;
      this.$emit('change', this.queryChips)
      this.showAddChipRow = false
    }
  },
  watch: {
    selectedQueryChips() {
      this.queryChips = this.selectedQueryChips
    }
  }
}
</script>
