<!--
Copyright 2024 Google Inc. All rights reserved.

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
  <v-container class="ma-0">
    <v-row>
      <v-col>
        <TsChartTypeSelect
          v-bind:aggregator="aggregatorType"
          v-bind:chart="selectedChartType"
          @selectedChartType="selectedChartType = $event"
        >
        </TsChartTypeSelect>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-text-field
          outlined
          label="Visualization title"
          v-model="selectedChartTitle"
          @input="$emit('selectedChartTitle', event)"
        ></v-text-field>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-text-field v-model="selectedHeight" outlined label="Height"></v-text-field>
      </v-col>
      <v-col>
        <v-text-field v-model="selectedWidth" outlined label="Width"></v-text-field>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-text-field v-model="selectedXTitle" outlined label="X-axis title"></v-text-field>
      </v-col>
      <v-col>
        <v-checkbox v-model="selectedShowXLabels" label="Show x-axis labels"></v-checkbox>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-text-field v-model="selectedYTitle" outlined label="Y-axis title"></v-text-field>
      </v-col>
      <v-col>
        <v-checkbox v-model="selectedShowYLabels" label="Show y-axis labels"></v-checkbox>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-checkbox v-model="selectedDataLabels" label="Show data labels"></v-checkbox>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import TsChartTypeSelect from './ChartTypeSelect.vue'

export default {
  components: {
    TsChartTypeSelect,
  },
  props: [
    'aggregatorType',
    'chartType',
    'title',
    'height',
    'width',
    'xTitle',
    'showXLabels',
    'yTitle',
    'showYLabels',
    'showDataLabels',
  ],
  data() {
    return {
      selectedChartType: this.chartType,
      selectedChartTitle: this.title,
      selectedHeight: this.height,
      selectedWidth: this.width,
      selectedXTitle: this.xTitle,
      selectedShowXLabels: this.showXLabels,
      selectedYTitle: this.yTitle,
      selectedShowYLabels: this.showYLabels,
      selectedDataLabels: this.showDataLabels,
    }
  },
  watch: {
    selectedChartType() {
      this.$emit('updateChartType', this.selectedChartType)
    },
    selectedChartTitle() {
      this.$emit('updateTitle', this.selectedChartTitle)
    },
    selectedHeight() {
      this.$emit('updateHeight', this.selectedHeight)
    },
    selectedWidth() {
      this.$emit('updateWidth', this.selectedWidth)
    },
    selectedXTitle() {
      this.$emit('updateXTitle', this.selectedXTitle)
    },
    selectedShowXLabels() {
      this.$emit('updateShowXLabels', this.selectedShowXLabels)
    },
    selectedYTitle() {
      this.$emit('updateYTitle', this.selectedYTitle)
    },
    selectedShowYLabels() {
      this.$emit('updateShowYLabels', this.selectedShowYLabels)
    },
    selectedDataLabels() {
      this.$emit('updateShowDataLabels', this.selectedDataLabels)
    },
  }
}
</script>
