<!--
Copyright 2021 Google Inc. All rights reserved.

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
    <ts-navbar-main>
      <template v-slot:left>
        {{ sketch.name }}
      </template>
    </ts-navbar-main>

    <ts-navbar-secondary currentAppContext="sketch" currentPage="aggregate"></ts-navbar-secondary>

    <ts-sketch-explore-aggregation @newAggregation="addAggregation($event)"></ts-sketch-explore-aggregation>

    <br /><br />

    <section class="section" v-if="allAggregations.length">
      <div class="container is-fluid">
        <span class="title is-5">Saved aggregations</span>
      </div>
    </section>

    <section class="section" v-for="aggregation in allAggregations" :key="aggregation.id">
      <div class="container is-fluid">
        <ts-aggregation-compact :aggregation="aggregation" :card-header="true"></ts-aggregation-compact>
      </div>
    </section>
  </div>
</template>

<script>
import TsSketchExploreAggregation from '../components/Aggregation/Aggregation'
import ApiClient from '../utils/RestApiClient'
import TsAggregationCompact from '../components/Aggregation/AggregationCompact'

export default {
  components: { TsSketchExploreAggregation, TsAggregationCompact },
  data() {
    return {
      aggregations: [],
      aggregationGroups: [],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    allAggregations() {
      const concat = (...arrays) => [].concat(...arrays.filter(Array.isArray))
      return concat(this.aggregations, this.aggregationGroups)
        .slice()
        .reverse()
    },
  },
  methods: {
    addAggregation(aggregation) {
      this.aggregations.push(aggregation)
    },
  },
  created: function() {
    ApiClient.getAggregations(this.sketch.id)
      .then(response => {
        this.aggregations = response.data.objects[0]
      })
      .catch(e => {
        console.error(e)
      })
    ApiClient.getAggregationGroups(this.sketch.id)
      .then(response => {
        this.aggregationGroups = response.data.objects
      })
      .catch(e => {
        console.error(e)
      })
  },
}
</script>
