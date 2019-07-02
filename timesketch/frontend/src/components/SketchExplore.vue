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
      <div class="container">
        <ts-navbar-secondary currentAppContext="sketch" currentPage="explore"></ts-navbar-secondary>
      </div>
    </section>

    <ts-sketch-explore-search :sketchId="sketchId"></ts-sketch-explore-search>

    <section class="section" v-if="searchInProgress">
      <div class="container">
        <div class="card">
          <div class="card-content">
            <span class="icon">
              <i class="fas fa-circle-notch fa-pulse"></i>
            </span>
            <span>Searching..</span>
          </div>
        </div>
      </div>
    </section>

    <section class="section" v-if="eventList.meta.es_time">
      <div class="container" v-if="!searchInProgress">
        <div class="card">
          <div class="card-content">
            <div v-if="totalTime">{{ totalHits }} events ({{ totalTime }}s)</div>
            <div v-if="totalHits > 0" style="margin-top:20px;"></div>
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
  props: ['sketchId'],
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
    },
    searchInProgress () {
      return this.$store.state.searchInProgress
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
