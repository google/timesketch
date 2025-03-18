<!--
Copyright 2025 Google Inc. All rights reserved.

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
  <v-select
    v-model="riskLevel"
    class="risk-level-selector text-uppercase font-weight-medium"
    rounded
    :disabled="disabled"
    hide-details
    small
    plain
    flat
    placeholder="Risk level"
    :min-width="riskLevel ? 'auto' : 85"
    :bg-color="riskColor"
    :items="[
      { value: 'high', title: 'High' },
      { value: 'medium', title: 'Medium' },
      { value: 'low', title: 'Low' },
      { value: 'clean', title: 'Clean' },
    ]"
    variant="solo"
    @update:modelValue="onChange"
  ></v-select>
</template>

<script>
import { riskColors } from "@/constants";

export default {
  props: {
    riskLevel: String,
  },
  data() {
    return {
      riskLevel: this.riskLevel,
    };
  },
  methods: {
    onChange(value) {
      this.$emit("update:riskLevel", value);
    },
  },
  computed: {
    riskColor() {
      return riskColors[this.riskLevel];
    },
  },
};
</script>

<style>
.risk-level-selector .v-field {
  font-size: 12px !important;
  padding: 5px 0 5px 10px !important;
}

.risk-level-selector .v-icon {
  margin: 0 !important;
}

.risk-level-selector .v-field .v-field__input {
  min-height: 20px !important;
  padding: 0;
}
</style>
