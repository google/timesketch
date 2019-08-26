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
  <div id="vega"></div>
</template>

<script>
import { default as vegaEmbed } from 'vega-embed'

export default {
  name: 'vega-lite-chart',
  props: ['vegaSpec'],
  components: {},
  watch: {
    vegaSpec: function (newVal, oldVal) {
      vegaEmbed('#vega', JSON.parse(this.vegaSpec), { actions: false })
    }
  }
}
</script>

<style lang="scss"></style>
