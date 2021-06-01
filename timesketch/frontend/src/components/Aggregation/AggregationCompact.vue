<!--
Copyright 2020 Google Inc. All rights reserved.

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
  <div class="card">
    <header class="card-header">
      <span class="card-header-title">
        {{ aggregation.name }}
        <span style="margin-left:15px; font-weight: normal;" v-if="aggParameters.start_time && aggParameters.end_time"
          >[{{ aggParameters.start_time }} &rarr; {{ aggParameters.end_time }}]</span
        >
        <ts-timeline-chip
          v-for="timeline in timelines"
          :key="timeline.id"
          :timeline="timeline"
          style="margin-left:10px;"
        ></ts-timeline-chip>
      </span>
    </header>
    <div class="card-content" ref="vegaChart">
      <ts-table-chart v-if="chartType === 'table'" :table-data="chartData"></ts-table-chart>
      <ts-vega-lite-chart v-if="chartType !== 'table'" :vegaSpec="vegaSpec"></ts-vega-lite-chart>
    </div>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsVegaLiteChart from './VegaLiteChart'
import TsTableChart from './TableChart'
import TsTimelineChip from '../Explore/TimelineChip'

export default {
  props: ['aggregation', 'cardHeader'],
  components: { TsVegaLiteChart, TsTableChart, TsTimelineChip },
  data() {
    return {
      vegaSpec: {},
      title: '',
      chartType: '',
      chartData: {},
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    aggParameters() {
      return JSON.parse(this.aggregation.parameters)
    },
    timelines() {
      let timelines = []
      if (this.aggParameters.index && Array.isArray(this.aggParameters.index)) {
        this.aggParameters.index.forEach(timelineId => {
          let timeline = this.sketch.active_timelines.find(timeline => timeline.id === timelineId)
          timelines.push(timeline)
        })
      }
      return timelines
    },
  },
  methods: {
    getVegaSpec: function() {
      let d = {
        aggregator_name: this.aggregation.agg_type,
        aggregator_parameters: this.aggregation.parameters,
      }
      ApiClient.runAggregator(this.sketch.id, d)
        .then(response => {
          let spec = response.data.meta.vega_spec
          spec.config.view.width = this.$refs.vegaChart.offsetWidth - 50
          spec.config.autosize = { type: 'fit', contains: 'padding' }
          this.vegaSpec = JSON.stringify(spec)
          this.title = response.data.meta.vega_chart_title
          this.chartType = response.data.meta.chart_type
          // Get the first key of the object.
          this.chartData = spec.datasets[Object.keys(spec.datasets)[0]]
        })
        .catch(e => {})
    },
  },
  mounted: function() {
    this.getVegaSpec()
  },
}
</script>
