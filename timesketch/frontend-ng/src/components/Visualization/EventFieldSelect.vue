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
  <v-autocomplete
    outlined
    v-model="selectedField"
    :items="mappedTimelineFields"
    label="Field name to aggregate"
    :loading="loadingFields"
    @input="$emit('selectedField', $event)"
  >
    <template
      #item="{ item, on, attrs }"
    >
      <v-list-item
        v-on="on"
        v-bind="attrs"
      >
        <v-list-item-avatar>
          <v-icon>
            {{ item.value.type === 'text' ? 'mdi-code-string' : 'mdi-pound-box' }}
          </v-icon>
        </v-list-item-avatar>
        <v-list-item-content>
          {{ item.text }}
        </v-list-item-content>
      </v-list-item>
    </template>
    <template
      #selection="{ item }"
    >
      <v-icon>
        {{ item.value.type === 'text' ? 'mdi-code-string' : 'mdi-pound-box' }}
      </v-icon>
      &nbsp; &nbsp; {{ item.text }}
    </template>
  </v-autocomplete>
</template>

<script>

export default {
  props: {
    field: {
      type: Object,
    },
    timelineFields: {
      type: Array,
      default: () => [],
    },
    loadingFields: {
        type: Boolean,
        default: false
    },
  },
  data() {
    return {
      selectedField: this.field,
    }
  },
  computed: {
    mappedTimelineFields() {
      const mappings = this.$store.state.meta.mappings;

      return this.timelineFields.map(field => {
        const mapping = mappings.find(m => m.field === field);
        const type = mapping ? mapping.type : 'unknown';
        return { text: field, value: { field, type } };
      });
    },
  },
  watch: {
    field() {
        this.selectedField = this.field
    },
    timelineFields(newFields) {
      if (!newFields || newFields.length === 0) {
          this.selectedField = null;
      }
    },
  }
}
</script>
