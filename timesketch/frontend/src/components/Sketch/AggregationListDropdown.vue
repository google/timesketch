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
  <b-dropdown ref="dropdown" animation="none" aria-role="menu" append-to-body>
    <a class="button" v-bind:class="{ 'is-rounded': isRounded}" slot="trigger">
      <span>+ Aggregation</span>
      <b-icon :icon="active ? 'chevron-up' : 'chevron-down'" style="font-size: 0.6em;"></b-icon>
    </a>
    <div class="modal-card" style="width:500px;color: var(--font-color-dark);">
      <section class="modal-card-body">
        <span class="dropdown-item" v-if="aggregations && aggregations.length < 1">No saved aggregations</span>
        <a class="dropdown-item" v-on:click="setActiveAggregation(agg)" v-for="agg in aggregations" :key="agg.id">
          <span>{{ agg.name }}</span>
        </a>
      </section>
    </div>
  </b-dropdown>
</template>

<script>
export default {
  props: ['isRounded', 'aggregations'],
  methods: {
    setActiveAggregation: function (aggregation) {
      this.$emit('addAggregation', aggregation)
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
