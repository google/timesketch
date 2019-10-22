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
    <ts-sketch-explore-event-list-item v-for="(event, index) in eventList.objects" :key="event._id" :event="event" :prevEvent="eventList.objects[index - 1]"></ts-sketch-explore-event-list-item>
  </div>
</template>

<script>
import TsSketchExploreEventListItem from './EventListItem'

export default {
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
    }
  }
}
</script>
