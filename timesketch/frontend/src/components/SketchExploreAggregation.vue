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
    <section class="section">
      <div class="container is-fluid">
        <ts-navbar-secondary style="margin-bottom: 10px;" currentAppContext="explore" currentPage="aggregation"></ts-navbar-secondary>
        <div class="card">
          <div class="card-content">
            <ts-sketch-explore-aggregator-list-dropdown @setActiveAggregator="updateAggregatorFormFields"></ts-sketch-explore-aggregator-list-dropdown>
            <br>
            <ts-dynamic-form :schema="schema" v-model="formData" @formSubmitted="getVegaSpec" :key="selectedAggregator" ref="vegaChart"></ts-dynamic-form>
            <br>
          </div>
          <div class="card">
            <div class="card-content">
              <ts-vega-lite-chart :vegaSpec="vegaSpec" v-if="showChart"></ts-vega-lite-chart>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsVegaLiteChart from './VegaLiteChart'
import TsDynamicForm from './DynamicForm'
import TsSketchExploreAggregatorListDropdown from './SketchExploreAggregatorListDropdown'

export default {
  name: 'ts-sketch-explore-aggregation',
  components: {
    TsDynamicForm,
    TsVegaLiteChart,
    TsSketchExploreAggregatorListDropdown
  },
  data () {
    return {
      schema: {},
      formData: {},
      vegaSpec: {},
      selectedAggregator: '',
      showChart: false
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
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
      this.selectedAggregator = aggregator.name
    },
    getVegaSpec: function () {
      this.showChart = true
      let d = {
        'aggregator_name': this.selectedAggregator,
        'aggregator_parameters': this.formData
      }
      ApiClient.runAggregator(this.sketch.id, d).then((response) => {
        let spec = response.data.meta.vega_spec
        spec.config.view.width = this.$refs.vegaChart.$el.offsetWidth
        spec.config.autosize = { type: 'fit', contains: 'padding' }
        this.vegaSpec = JSON.stringify(spec)
      }).catch((e) => {})
    }
  }

}
</script>

<style lang="scss"></style>
