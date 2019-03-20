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
      <li style="padding:15px;" v-for="sketch in sketches" :key="sketch.id">
        <div class="is-pulled-right" style="margin-top:10px;">
          <span class="is-size-7">{{ sketch.user.username }}</span>
        </div>
        <div>
          <router-link :to="{ name: 'SketchOverview', params: {sketchId: sketch.id } }"><strong>{{ sketch.name }}</strong></router-link>
          <br>
          <span class="is-size-7">Last activity {{ sketch.updated_at }}</span>
        </div>
      </li>
    </ul>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'

export default {
  name: 'ts-home-sketch-list',
  data () {
    return {
      sketches: []
    }
  },
  created: function () {
    ApiClient.getSketchList().then((response) => {
      this.$store.dispatch('resetState')
      this.sketches = response.data.objects[0]
    }).catch((e) => {
      console.error(e)
    })
  }

}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
  ul.content-list {
      list-style: none;
  }

  ul.content-list>li {
      padding-top: 15px;
      padding-bottom: 15px;
      border-bottom: 1px solid #eee;
      display: block;
      margin: 0;
  }

  ul.content-list>li:hover {
      background: #fcfcfc;
  }

  ul.content-list>li:last-child { border-bottom: none; }
</style>
