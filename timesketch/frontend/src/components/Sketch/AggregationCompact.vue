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
    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <header class="card-header">
            <span class="card-header-title">
              {{ aggName }}
            </span>
          </header>
          <div class="card-content" ref="vegaChart">
            <ts-vega-lite-chart :vegaSpec="vegaSpec"></ts-vega-lite-chart>
          </div>
        </div>
      </div>
    </section>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsVegaLiteChart from './VegaLiteChart'

export default {
  props: ['aggName', 'aggParameters'],
  components: {TsVegaLiteChart},
  data () {
    return {
      vegaSpec: {}
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    }
  },
  methods: {
    getVegaSpec: function () {
      let d = {
        'aggregator_name': this.aggName,
        'aggregator_parameters': this.aggParameters
      }
      ApiClient.runAggregator(this.sketch.id, d).then((response) => {
        let spec = response.data.meta.vega_spec
        console.log(this.$refs)
        spec.config.view.width = this.$refs.vegaChart.offsetWidth - 50
        spec.config.autosize = { type: 'fit', contains: 'padding' }
        this.vegaSpec = JSON.stringify(spec)
      }).catch((e) => {})
    }
  },
  mounted: function () {
    this.getVegaSpec()
  }

}
</script>
