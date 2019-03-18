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
    <div v-if="totalTime">{{ totalHits }} events ({{ totalTime }}s)</div>
    <div v-if="totalHits > 0" style="margin-top:20px;">
      <ts-sketch-explore-event-list-item v-for="event in eventList.objects" :key="event._id" :event="event"></ts-sketch-explore-event-list-item>
    </div>
  </div>
</template>

<script>
import TsSketchExploreEventListItem from './SketchExploreEventListItem'

export default {
  name: 'ts-sketch-explore-event-list',
  components: {
    TsSketchExploreEventListItem
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
    totalHits () {
      return this.eventList.meta.es_total_count || 0
    },
    totalTime () {
      return this.eventList.meta.es_time / 1000 || 0
    }
  }
}
</script>

<style lang="scss"></style>
