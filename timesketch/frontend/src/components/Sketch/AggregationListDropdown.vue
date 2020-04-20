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
  <div class="dropdown" v-bind:class="{'is-active': dropdownActive}">
    <div class="dropdown-trigger">
      <a class="button" v-bind:class="{'is-rounded': isRounded}" aria-haspopup="true" aria-controls="dropdown-menu" v-on:click="dropdownActive = !dropdownActive">
        <span>{{ title || 'Aggregations' }}</span>
        <span class="icon is-small">
          <i class="fas fa-angle-down" aria-hidden="true"></i>
        </span>
      </a>
    </div>
    <div class="dropdown-menu" id="dropdown-menu" role="menu">
      <div class="dropdown-content">
        <span class="dropdown-item" v-if="aggregations && aggregations.length < 1">No saved aggregations</span>
        <a class="dropdown-item" v-on:click="setActiveAggregation(agg)" v-for="agg in aggregations" :key="agg.id">
          <span>{{ agg.name }}</span>
        </a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['isRounded', 'title', 'aggregations'],
  data () {
    return {
      dropdownActive: false
    }
  },
  methods: {
    setActiveAggregation: function (aggregation) {
      this.$emit('addAggregation', aggregation)
      this.viewListDropdownActive = false
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
