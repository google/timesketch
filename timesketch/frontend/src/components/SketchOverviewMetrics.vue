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
  <nav class="level">
    <div class="level-item has-text-centered">
      <div>
        <p class="heading">Timelines</p>
        <p class="title">{{ timelines && timelines.length ? timelines.length: 0 }}</p>
      </div>
    </div>
    <div class="level-item has-text-centered">
      <div>
        <p class="heading">Views</p>
        <p class="title">{{ views && views.length ? views.length: 0  }}</p>
      </div>
    </div>
    <div class="level-item has-text-centered">
      <div>
        <p class="heading">Stories</p>
        <p class="title">{{ views && stories.length ? stories.length: 0  }}</p>
      </div>
    </div>
    <div class="level-item has-text-centered">
      <div>
        <p class="heading">Events</p>
        <p class="title">{{ count | compactNumber }}</p>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'ts-sketch-overview-metrics',
  props: ['timelines', 'views', 'stories', 'count']
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
