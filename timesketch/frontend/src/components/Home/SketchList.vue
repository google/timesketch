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
    <!--
    <b-table
      :data="sketches"
      :per-page="perPage"
      paginated
      pagination-simple
      pagination-position="bottom"
      default-sort-direction="desc"
      icon-pack="fas"
      icon-prev="chevron-left"
      icon-next="chevron-right">
      <b-table-column field="name" label="Name" v-slot="props">
        <router-link :to="{ name: 'SketchOverview', params: {sketchId: props.row.id } }"><strong>{{ props.row.name }}</strong></router-link>
      </b-table-column>
      <b-table-column field="status" v-slot="props">
          <span v-if="props.row.status === 'archived'">
            <b-tag>{{ props.row.status }}</b-tag>
          </span>
      </b-table-column>
      <b-table-column field="user" label="Created by" width="200" v-slot="props">
        {{ props.row.user }}
      </b-table-column>
      <b-table-column field="updated_at" label="Last activity" width="200" v-slot="props">
        {{ new Date(props.row.updated_at) | moment("YYYY-MM-DD HH:mm") }}
      </b-table-column>

      <template slot="bottom-left">
        <div class="has-text-right">
          <div class="level" >
            <div class="level-left" style="margin-right: 10px;">
              Rows per page:
            </div>
            <div class="level-right">
              <b-select class="is-pulled-left" placeholder="Rows per page" v-model="perPage" size="is-small">
                <option v-bind:value="perPage">{{ perPage }}</option>
                <option value="20">20</option>
                <option value="40">40</option>
                <option value="80">80</option>
                <option value="100">100</option>
                <option value="200">200</option>
                <option value="500">500</option>
              </b-select>
            </div>
          </div>
        </div>
      </template>
    </b-table>
    -->

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
      v-if="numSketches > 20"
      v-model="currentPage"
      @change="paginate"
      :total="numSketches"
      :simple="true"
      :per-page="20"
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
      currentPage: 1
    }
  },
  methods: {
    getSketches: function () {
      ApiClient.getSketchList(this.scope, this.currentPage, this.searchQuery).then((response) => {
        this.sketches = response.data.objects
        this.numSketches = response.data.meta.num_hits
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
