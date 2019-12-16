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
      <li style="padding:10px;border-bottom:none;" v-for="story in sketch.stories" :key="story.id">
        <div>
          <router-link :to="{ name: 'SketchStoryContent', params: {sketchId: sketch.id, storyId: story.id}}"><strong>{{ story.title }}</strong></router-link>
          <br>
          <span class="is-size-7">Last activity {{ story.updated_at | moment("YYYY-MM-DD HH:mm") }}</span>
        </div>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  data () {
    return {
      stories: []
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    }
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
