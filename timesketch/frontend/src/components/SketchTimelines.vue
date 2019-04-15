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
        <ts-navbar-secondary currentAppContext="sketch" currentPage=""></ts-navbar-secondary>
      </div>
    </section>

    <!-- Active Timelines -->
    <section class="section">
      <div class="container">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Active Timelines</p>
          </header>
          <div class="card-content">
            <ts-timeline-list :timelines="sketch.timelines"></ts-timeline-list>
          </div>
        </div>
      </div>
    </section>

    <!-- Timelines to add -->
    <section class="section">
      <div class="container">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Timelines to add</p>
          </header>
          <div class="card-content">
            <ul class="content-list">
              <li style="padding:10px;" v-for="searchindex in availableSearchIndices" :key="searchindex.id">
                  <div class="ts-timeline-color-box is-pulled-left has-text-centered" style="background-color:#f5f5f5;cursor:pointer;" v-on:click="addTimelineToSketch(searchindex)">
                    <span style="margin-top:10px;color:#d1d1d1;" class="icon"><i class="fas fa-plus"></i></span>
                  </div>
                  <strong>{{ searchindex.name }}</strong>
                  <br>
                  <span class="is-size-7">
                    Created {{ searchindex.updated_at | moment("YYYY-MM-DD HH:mm") }}
                  </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsTimelineList from './SketchOverviewTimelineList'

export default {
  name: 'ts-sketch-overview',
  components: {
    TsTimelineList
  },
  data () {
    return {
      availableSearchIndices: []
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    }
  },
  methods: {
    addTimelineToSketch (searchIndex) {
      ApiClient.createSketchTimeline(this.sketch.id, searchIndex.id).then((response) => {
        this.$store.commit('updateSketch', this.sketch.id)
        const idx = this.availableSearchIndices.indexOf(searchIndex)
        this.availableSearchIndices.splice(idx, 1)
      }).catch((e) => {
        console.error(e)
      })
    }
  },
  created: function () {
    ApiClient.getSearchIndexList().then((response) => {
      let allSearchIndices = response.data.objects[0]
      let sketchSearchIndices = this.$store.state.sketch.timelines.map(x => x.searchindex.index_name)
      allSearchIndices.forEach(function (searchindex) {
        if (!sketchSearchIndices.includes(searchindex.index_name)) {
          if (searchindex.status[0].status === 'ready') {
            this.push(searchindex)
          }
        }
      }, this.availableSearchIndices)
    }).catch((e) => {
      console.error(e)
    })
  }
}
</script>

<style lang="scss"></style>
