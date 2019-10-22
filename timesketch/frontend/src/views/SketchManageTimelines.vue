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
    <section class="section" v-if="!hideNavigation">
      <div class="container is-fluid">
        <ts-navbar-secondary currentAppContext="sketch" currentPage=""></ts-navbar-secondary>
      </div>
    </section>

    <!-- Active Timelines -->
    <section class="section" v-if="sketch.timelines.length">
      <div class="container is-fluid">
        <div class="card" style="min-height:160px;">
          <header class="card-header">
            <p class="card-header-title">Active Timelines</p>
            <p class="is-pulled-right" style="padding: 0.75rem;font-weight: bold;color: #777777;">{{ count | compactNumber }} events</p>
          </header>
          <div class="card-content">
            <ts-timeline-list @remove-timeline="makeTimelineAvailable" :timelines="sketch.timelines" :controls="true"></ts-timeline-list>
          </div>
        </div>
      </div>
    </section>

    <!-- Timelines to add -->
    <section class="section">
      <div class="container is-fluid">
        <div class="card" style="min-height:160px;">
          <header class="card-header">
            <p class="card-header-title">Add Timelines</p>
          </header>
          <div class="card-content" style="background-color:rgba(44,255,0,0.08);">
            <p>
              Upload a new timeline or choose an existing one from the list below. You can upload either a Plaso storage file, JSONL, or a CSV file.
              <br>
              If you are uploading a CSV or JSONL file make sure to read the <a href="https://github.com/google/timesketch/blob/master/docs/Users-Guide.md#adding-timelines" rel="noreferrer" target="_blank">documentation</a> to learn what columns are needed.
            </p>
            <br>
            <ts-upload-timeline-form></ts-upload-timeline-form>
          </div>
          <div class="card-content" v-if="availableSearchIndices.length">
            <ul class="content-list">
              <transition-group name="list" tag="p">
                <li style="padding:10px;" v-for="searchindex in availableSearchIndices" :key="searchindex.id">
                  <div class="ts-timeline-color-box is-pulled-left has-text-centered" style="background-color:#f5f5f5;cursor:pointer;" v-on:click="addTimelineToSketch(searchindex)">
                    <span style="margin-top:10px;color:#d1d1d1;" class="icon"><i class="fas fa-plus"></i></span>
                  </div>
                  <div class="is-pulled-right" style="margin-top:10px;">
                    <button v-on:click="addTimelineToSketch(searchindex)" class="button is-small is-rounded is-success is-outlined">Add</button>
                  </div>
                    <strong>{{ searchindex.name }}</strong>
                    <br>
                    <span class="is-size-7">
                      Created {{ searchindex.updated_at | moment("YYYY-MM-DD HH:mm") }}
                    </span>
                </li>
              </transition-group>
            </ul>
          </div>
          <div class="card-content" v-if="!availableSearchIndices.length">
            <p style="color:#777; font-weight: bold">No timelines available</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsTimelineList from '../components/Sketch/TimelineList'
import TsUploadTimelineForm from '../components/Sketch/UploadForm'

export default {
  name: 'ts-sketch-manage-timelines',
  props: ['hideNavigation'],
  components: {
    TsTimelineList,
    TsUploadTimelineForm
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
    },
    count () {
      return this.$store.state.count
    }
  },
  methods: {
    addTimelineToSketch (searchIndex) {
      ApiClient.createSketchTimeline(this.sketch.id, searchIndex.id).then((response) => {
        const idx = this.availableSearchIndices.indexOf(searchIndex)
        this.availableSearchIndices.splice(idx, 1)
        this.$store.commit('updateSketch', this.sketch.id)
      }).catch((e) => {
        console.error(e)
      })
    },
    makeTimelineAvailable (event) {
      this.availableSearchIndices.unshift(event.searchindex)
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

<style lang="scss">
.list-item {
  display: inline-block;
  margin-right: 10px;
}
.list-enter-active, .list-leave-active {
  transition: all 0.5s;
}
.list-enter, .list-leave-to /* .list-leave-active below version 2.1.8 */ {
  opacity: 0;
  transform: translateY(-30px);
}
</style>
