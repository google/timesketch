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
  <div>

    <b-modal :active.sync="showSaveModal" :width="640" scroll="keep">
      <div class="card">
        <header class="card-header">
          <p class="card-header-title">Save aggregation</p>
        </header>
        <div class="card-content">
          <div class="content">
            <form v-on:submit.prevent="save()">
              <div class="field">
                <label class="label">Name</label>
                <div class="control">
                  <input v-model="aggregationName" class="input" type="text" required placeholder="Name your aggregation" autofocus>
                </div>
              </div>
              <div class="field">
                <div class="control">
                  <input class="button is-success" type="submit" value="Save">
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </b-modal>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <header class="card-header" v-on:click="showAggregations = !showAggregations" style="cursor: pointer">
            <span class="card-header-title">
              <span class="icon is-small"><i class="fas fa-chart-bar"></i></span>
              <span style="margin-left:10px;">Insights</span>
            </span>
            <span class="card-header-icon">
              <span class="icon">
                <i class="fas fa-angle-down" v-if="!showAggregations" aria-hidden="true"></i>
                <i class="fas fa-angle-up" v-if="showAggregations" aria-hidden="true"></i>
              </span>
            </span>
          </header>
          <div class="card-content" v-show="showAggregations">
            <ts-sketch-explore-aggregator-list-dropdown @setActiveAggregator="updateAggregatorFormFields"></ts-sketch-explore-aggregator-list-dropdown>
            <br>
            <ts-dynamic-form :schema="schema" v-model="formData" @formSubmitted="getVegaSpec" :key="selectedAggregator.name" ref="vegaChart"></ts-dynamic-form>
          </div>
        </div>
      </div>
    </section>
    <section class="section" v-show="showChart && showAggregations && Object.keys(vegaSpec).length !== 0">
      <div class="container is-fluid">
        <div class="card">
          <header class="card-header">
            <span class="card-header-title">
              {{ selectedAggregator.display_name }}
            </span>
            <span class="card-header-icon">
            <a class="button is-rounded is-small" v-on:click="showSaveModal =! showSaveModal">
              <span class="icon is-small">
                <i class="fas fa-save"></i>
              </span>
              <span>Save</span>
            </a>
            </span>
          </header>
          <div class="card-content">
            <ts-table-chart v-show="chartType === 'table'" :table-data="chartData"></ts-table-chart>
            <ts-vega-lite-chart v-show="chartType !== 'table'" :vegaSpec="vegaSpec"></ts-vega-lite-chart>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsVegaLiteChart from './VegaLiteChart'
import TsDynamicForm from './DynamicForm'
import TsSketchExploreAggregatorListDropdown from './AggregatorListDropdown'
import TsTableChart from './TableChart'

export default {
  props: ['showAggregations'],
  components: {
    TsDynamicForm,
    TsVegaLiteChart,
    TsSketchExploreAggregatorListDropdown,
    TsTableChart
  },
  data () {
    return {
      schema: {},
      formData: {},
      vegaSpec: {},
      selectedAggregator: '',
      showChart: false,
      showSaveModal: false,
      aggregationName: '',
      chartType: '',
      chartData: {}
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    }
  },
  methods: {
    updateAggregatorFormFields: function (aggregator) {
      this.showChart = false
      let data = {}
      this.schema = aggregator.form_fields
      this.schema.forEach(function (field) {
        data[field.name] = field.default_value
      })
      this.formData = data
      this.selectedAggregator = aggregator
    },
    getVegaSpec: function () {
      this.showChart = true
      let d = {
        'aggregator_name': this.selectedAggregator.name,
        'aggregator_parameters': this.formData
      }
      ApiClient.runAggregator(this.sketch.id, d).then((response) => {
        let spec = response.data.meta.vega_spec
        spec.config.view.width = this.$refs.vegaChart.$el.offsetWidth
        spec.config.autosize = { type: 'fit', contains: 'padding' }
        this.vegaSpec = JSON.stringify(spec)
        this.chartType = response.data.meta.chart_type
        // Get the first key of the object.
        this.chartData = spec.datasets[Object.keys(spec.datasets)[0]]
      }).catch((e) => {})
    },
    save: function () {
      this.showSaveModal = false
      ApiClient.saveAggregation(this.sketch.id, this.selectedAggregator, this.aggregationName, this.formData).then((response) => {
        let aggregation = response.data.objects[0]
        this.$store.state.sketch.aggregations.push(aggregation)
        this.aggregationName = ''
      }).catch((e) => {})
    }
  }

}
</script>
