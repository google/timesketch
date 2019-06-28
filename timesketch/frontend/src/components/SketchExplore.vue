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
      <div class="container">
        <ts-navbar-secondary currentAppContext="sketch" currentPage="explore"></ts-navbar-secondary>
      </div>
    </section>

    <ts-sketch-explore-search :sketchId="sketchId"></ts-sketch-explore-search>

    <section class="section">
      <div class="container">
        <div class="card">
          <div class="card-content">
            <ts-sketch-explore-aggregator-list-dropdown @setActiveAggregator="updateAggregatorFormFields"></ts-sketch-explore-aggregator-list-dropdown>
            <ts-dynamic-form :schema="schema" v-model="formData" @formSubmitted="getVegaSpec" :key="selectedAggregator" ref="vegaChart"></ts-dynamic-form>
            <br>
            <ts-vega-lite-chart :vegaSpec="vegaSpec" v-if="showChart"></ts-vega-lite-chart>
          </div>
        </div>
      </div>
    </section>

    <section class="section" v-if="searchInProgress">
      <div class="container">
        <div class="card">
          <div class="card-content">
            <span class="icon">
              <i class="fas fa-circle-notch fa-pulse"></i>
            </span>
            <span>Searching..</span>
          </div>
        </div>
      </div>
    </section>

    <section class="section" v-if="eventList.meta.es_time">
      <div class="container" v-if="!searchInProgress">
        <div class="card">
          <div class="card-content">
            <div v-if="totalTime">{{ totalHits }} events ({{ totalTime }}s)</div>
            <div v-if="totalHits > 0" style="margin-top:20px;"></div>
            <ts-sketch-explore-event-list></ts-sketch-explore-event-list>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsSketchExploreSearch from './SketchExploreSearch'
import TsSketchExploreEventList from './SketchExploreEventList'
import TsVegaLiteChart from './VegaLiteChart'
import TsDynamicForm from './DynamicForm'
import TsSketchExploreAggregatorListDropdown from './SketchExploreAggregatorListDropdown'

export default {
  name: 'ts-sketch-explore',
  props: ['sketchId'],
  components: {
    TsSketchExploreSearch,
    TsSketchExploreEventList,
    TsVegaLiteChart,
    TsDynamicForm,
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
    },
    eventList () {
      return this.$store.state.eventList
    },
    searchInProgress () {
      return this.$store.state.searchInProgress
    },
    totalHits () {
      return this.eventList.meta.es_total_count || 0
    },
    totalTime () {
      return this.eventList.meta.es_time / 1000 || 0
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
      ApiClient.runAggregator(this.sketchId, d).then((response) => {
        let spec = response.data.meta.vega_spec
        spec.config.view.width = this.$refs.vegaChart.$el.offsetWidth
        spec.config.autosize = { type: 'fit', contains: 'padding' }
        this.vegaSpec = JSON.stringify(spec)
      }).catch((e) => {})
      // this.vegaSpec = '{"config": {"view": {"width": 800, "height": 600}, "mark": {"tooltip": null}}, "layer": [{"mark": "bar", "encoding": {"x": {"type": "quantitative", "field": "count"}, "y": {"type": "nominal", "field": "filename"}}}, {"mark": {"type": "text", "align": "left", "baseline": "middle", "dx": 3}, "encoding": {"text": {"type": "quantitative", "field": "count"}, "x": {"type": "quantitative", "field": "count"}, "y": {"type": "nominal", "field": "filename"}}}], "data": {"values": [{"filename": "/Windows/System32/config/SOFTWARE", "count": 252568}, {"filename": "/Windows/System32/config/COMPONENTS", "count": 86634}, {"filename": "/Windows/System32/config/SYSTEM", "count": 29476}, {"filename": "/Windows/System32/winevt/Logs/Microsoft-Windows-Store%4Operational.evtx", "count": 27646}, {"filename": "/Windows/System32/config/DRIVERS", "count": 27240}, {"filename": "/Windows/System32/SMI/Store/Machine/SCHEMA.DAT", "count": 15856}, {"filename": "/Windows/System32/winevt/Logs/Security.evtx", "count": 14623}, {"filename": "TransportSecurity", "count": 12470}, {"filename": "/Windows/InfusedApps/Packages/Microsoft.MicrosoftOfficeHub_17.8918.5926.0_x64__8wekyb3d8bbwe/Registry.dat", "count": 11600}, {"filename": "/Windows/Provisioning/Microsoft-Desktop-Provisioning.dat", "count": 9419}]}, "$schema": "https://vega.github.io/schema/vega-lite/v3.3.0.json"}'
    }
  }
}
</script>

<style lang="scss"></style>
