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
  <div class="field">
    <div class="control">
      <div class="select">
        <select v-model="selected" @change="setActiveAggregator()">
          <option disabled>Choose aggregator</option>
          <option v-for="(aggregator, name) in meta.aggregators" :key="aggregator.id">
            {{ name }}
          </option>
        </select>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ts-sketch-explore-aggregator-list-dropdown',
  props: ['isRounded', 'title'],
  data () {
    return {
      selected: 'Choose aggregator',
      selectedChart: ''
    }
  },
  methods: {
    setActiveAggregator: function () {
      let aggregatorClone = JSON.parse(JSON.stringify(this.meta.aggregators[this.selected]))
      aggregatorClone.name = this.selected
      this.$emit('setActiveAggregator', aggregatorClone)
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
