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
          :aggregator="aggregatorType"
          :chart="selectedChartType"
          @selectedChartType="selectedChartType = $event"
          required
          :rules="[rules.required]"
        >
        </TsChartTypeSelect>
      </v-col>
    </v-row>
    <v-row class="my-4">
      <v-btn small icon @click="selectedShowOptions = !selectedShowOptions" class="ml-2">
        <v-icon v-if="selectedShowOptions" title="Hide Chart Options">mdi-chevron-up</v-icon>
        <v-icon v-else title="Show Chart Options">mdi-chevron-down</v-icon>
      </v-btn>
      <span v-if="selectedShowOptions" @click="selectedShowOptions = !selectedShowOptions" class="chart-options-trigger">Hide Chart Options</span>
      <span v-else @click="selectedShowOptions = !selectedShowOptions" class="chart-options-trigger">Show Chart Options</span>
    </v-row>
    <v-expand-transition>
      <div v-if="selectedShowOptions">
        <v-row>
          <v-col>
            <v-text-field
              v-model.number="selectedHeight"
              outlined
              label="Height"
              type="number"
            ></v-text-field>
          </v-col>
          <v-col>
            <v-text-field
              v-model.number="selectedWidth"
              outlined
              label="Width"
              type="number"
            ></v-text-field>
          </v-col>
        </v-row>
        <v-row class="mt-n10">
          <v-col>
            <v-text-field
              v-model="selectedYTitle"
              outlined
              label="Y-axis title"
            >
            </v-text-field>
          </v-col>
          <v-col>
            <v-text-field
              v-model="selectedXTitle"
              outlined
              label="X-axis title"
            ></v-text-field>
          </v-col>
        </v-row>
        <v-row class="mt-n14">
          <v-col>
            <v-checkbox
              v-model="selectedDataLabels"
              label="Show data labels"
            >
            </v-checkbox>
          </v-col>
          <v-col>
            <v-checkbox
              v-model="selectedShowYLabels"
              label="Show y-axis labels"
            >
            </v-checkbox>
          </v-col>
          <v-col>
            <v-checkbox
              v-model="selectedShowXLabels"
              label="Show x-axis labels"
            >
            </v-checkbox>
          </v-col>
        </v-row>
      </div>
    </v-expand-transition>
  </v-container>
</template>

<script>
import TsChartTypeSelect from './ChartTypeSelect.vue'

export default {
  components: {
    TsChartTypeSelect,
  },
  props: {
    aggregatorType: {
      type: String,
    },
    chartType: {
      type: String,
    },
    height: {
      type: Number,
      default: 640,
    },
    showDataLabels: {
      type: Boolean,
      default: true,
    },
    showOptions: {
      type: Boolean,
      default: false,
    },
    showXLabels: {
      type: Boolean,
      default: true,
    },
    showYLabels: {
      type: Boolean,
      default: true,
    },
    title: {
      type: String,
    },
    width: {
      type: Number,
      default: 800,
    },
    xTitle: {
      type: String,
    },
    yTitle: {
      type: String,
    }
  },
  data() {
    return {
      rules: {
          required: value => !!value || 'Required.',
      },
      selectedChartType: this.chartType,
      selectedChartTitle: this.title,
      selectedDataLabels: this.showDataLabels,
      selectedHeight: this.height,
      selectedShowOptions: this.showOptions,
      selectedShowXLabels: this.showXLabels,
      selectedShowYLabels: this.showYLabels,
      selectedWidth: this.width,
      selectedXTitle: this.xTitle,
      selectedYTitle: this.yTitle,
    }
  },
  watch: {
    aggregatorType() {
      this.selectedAggregator = this.aggregatorType
    },
    chartType() {
      this.selectedChartType = this.chartType
    },
    height() {
      this.selectedHeight = this.height
    },
    selectedChartType() {
      this.$emit('updateChartType', this.selectedChartType)
    },
    selectedChartTitle() {
      this.$emit('updateTitle', this.selectedChartTitle)
    },
    selectedDataLabels() {
      this.$emit('updateShowDataLabels', this.selectedDataLabels)
    },
    selectedHeight() {
      this.$emit('updateHeight', this.selectedHeight)
    },
    selectedShowXLabels() {
      this.$emit('updateShowXLabels', this.selectedShowXLabels)
    },
    selectedShowYLabels() {
      this.$emit('updateShowYLabels', this.selectedShowYLabels)
    },
    selectedWidth() {
      this.$emit('updateWidth', this.selectedWidth)
    },
    selectedXTitle() {
      this.$emit('updateXTitle', this.selectedXTitle)
    },
    selectedYTitle() {
      this.$emit('updateYTitle', this.selectedYTitle)
    },
    showDataLabels() {
      this.selectedDataLabels = this.showDataLabels
    },
    showXLabels() {
      this.selectedShowXLabels = this.showXLabels
    },
    showYLabels() {
      this.selectedShowYLabels = this.showYLabels
    },
    title() {
      this.selectedChartTitle = this.title
    },
    width() {
      this.selectedWidth = this.width
    },
    xTitle() {
      this.selectedXTitle = this.xTitle
    },
    yTitle() {
      this.selectedYTitle = this.yTitle
    },
  }
}
</script>

<style lang="scss">
.chart-options-trigger {
  display: flex;
  cursor: pointer;
  align-items: center;
}
</style>
