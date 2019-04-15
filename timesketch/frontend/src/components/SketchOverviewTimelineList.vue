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
    <ul class="content-list">
      <li style="padding:10px;" v-for="timeline in timelines" :key="timeline.id">
        <div>
          <div class="ts-timeline-color-box is-pulled-left" v-bind:style="{ 'background-color': '#' + timeline.color}"></div>
          <div v-if="controls" class="is-pulled-right" style="margin-top:10px;">
            <button v-on:click="removeTimelineFromSketch(timeline)" class="button is-small is-rounded is-danger is-outlined">Delete</button>
          </div>
          <router-link :to="{ name: 'SketchExplore', query: {index: timeline.searchindex.index_name}}"><strong>{{ timeline.name }}</strong></router-link>
          <br>
          <span class="is-size-7">
            Added {{ timeline.updated_at | moment("YYYY-MM-DD HH:mm") }}
          </span>
        </div>
      </li>
    </ul>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

export default {
  name: 'ts-sketch-overview-timeline-list',
  props: ['timelines', 'controls'],
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    }
  },
  methods: {
    removeTimelineFromSketch (timeline) {
      ApiClient.deleteSketchTimeline(this.sketch.id, timeline.id).then((response) => {
        this.$store.commit('updateSketch', this.sketch.id)
        this.$emit('removedTimeline', timeline)
      }).catch((e) => {
        console.error(e)
      })
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
