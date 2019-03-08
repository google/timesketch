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
          <strong>{{ timeline.name }}</strong>
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
export default {
  name: 'ts-timeline-list',
  props: ['sketchId', 'timelines']
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
  .ts-timeline-color-box {
    width:43px;
    height:43px;
    margin-top: 2px;
    margin-right: 10px;
    border-radius: 4px;
  }

  ul.content-list {
      list-style: none;
  }

  ul.content-list>li {
      padding-top: 5px;
      padding-bottom: 5px;
      border-bottom: 1px solid #eee;
      display: block;
      margin: 0;
  }

  ul.content-list>li:hover {
      background: #fcfcfc;
  }

  ul.content-list>li:last-child { border-bottom: none; }
</style>
