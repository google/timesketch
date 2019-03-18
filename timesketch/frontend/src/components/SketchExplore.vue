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

    <section class="section">
      <div class="container is-fluid">
        <ts-navbar-secondary currentAppContext="sketch" currentPage="explore"></ts-navbar-secondary>
      </div>
    </section>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <ts-sketch-explore-search></ts-sketch-explore-search>
          </div>
        </div>
      </div>
    </section>

    <section class="section" v-if="eventList.meta.es_time">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <ts-sketch-explore-event-list></ts-sketch-explore-event-list>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import TsSketchExploreSearch from './SketchExploreSearch'
import TsSketchExploreEventList from './SketchExploreEventList'

export default {
  name: 'ts-sketch-explore',
  components: {
    TsSketchExploreSearch,
    TsSketchExploreEventList
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

<style lang="scss"></style>
