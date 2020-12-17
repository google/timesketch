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
    <div v-if="!sketches.length">
      No {{ scope }} investigations found
    </div>

    <ul class="content-list">
      <li class="list-item" v-for="sketch in sketches" :key="sketch.id" style="padding:20px;">
        <div class="columns">
          <div class="column is-8">
            <router-link :to="{ name: 'SketchOverview', params: {sketchId: sketch.id } }"><strong>{{ sketch.name }}</strong></router-link>
            <div class="description">{{ sketch.description }}</div>
          </div>
          <div class="column">
            <strong style="color:var(--default-font-color)">Created by:</strong> {{ sketch.user }}
            <div style="font-size: 0.9em;">{{ sketch.created_at | moment("YYYY-MM-DD")}}</div>
          </div>
          <div class="column" style="text-align: right;">
            <span class="button is-small is-rounded is-light" style="border-radius: 20px;margin-top:10px;">
              <span v-if="sketch.status === 'archived'">
                Archived
              </span>
              <span v-else-if="sketch.last_activity">
                Active {{ $moment.utc(sketch.last_activity).local().fromNow() }}
              </span>
              <span v-else-if="!sketch.last_activity">
                No activity yet
              </span>
            </span>
            <div></div>
          </div>
        </div>
      </li>
    </ul>

    <br>
    <b-pagination class="is-right"
      v-if="numSketches > perPage"
      v-model="currentPage"
      @change="paginate"
      :total="numSketches"
      :simple="true"
      :per-page="perPage"
      size="is-small">
    </b-pagination>

  </div>

</template>

<script>
import ApiClient from "../../utils/RestApiClient"
import StoryList from "../Sketch/StoryList"

export default {
  components: {StoryList},
  props: ['scope', 'searchQuery'],
  data () {
    return {
      sketches: [],
      numSketches: 0,
      currentPage: 1,
      perPage: 10
    }
  },
  methods: {
    getSketches: function () {
      ApiClient.getSketchList(this.scope, this.currentPage, this.searchQuery).then((response) => {
        this.sketches = response.data.objects
        this.numSketches = response.data.meta.total_items
      }).catch((e) => {
        console.error(e)
      })
    },
    paginate: function () {
      this.getSketches()
    },
  },
  created() {
      this.getSketches()
  },
  watch: {
    searchQuery: function () {
      if (this.scope === 'search') {
        this.getSketches()
      }
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">

.description {
  display: -webkit-box;
  font-size: 0.9em;
  overflow: hidden;
  max-width: 35ch;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

</style>
