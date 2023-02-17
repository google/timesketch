<!--
Copyright 2023 Google Inc. All rights reserved.

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

<!--
 Canvas is a routing component to keep views alive and to support communication between
 them via Eventbus.
-->
<template>
  <div>
    <div v-show="currentRouteName === 'Explore'">
      <explore :sketch-id="sketchId"></explore>
    </div>
    <div v-show="currentRouteName === 'Intelligence'">
      <threat-intel :sketch-id="sketchId"></threat-intel>
    </div>
    <div v-show="currentRouteName === 'Graph'">
      <graph></graph>
    </div>
  </div>
</template>

<script>
import Explore from './Explore'
import ThreatIntel from './ThreatIntel'
import Graph from './Graph'

export default {
  components: {
    Explore,
    ThreatIntel,
    Graph,
  },
  props: ['sketchId'],
  computed: {
    currentRouteName() {
      return this.$route.name
    },
  },
}
</script>
