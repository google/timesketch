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
        <p class="title">{{ sketch.active_timelines.length }}</p>
      </div>
    </div>
    <div class="level-item has-text-centered">
      <div>
        <p class="heading">Views</p>
        <p class="title">{{ meta.views.length }}</p>
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
import ApiClient from '../utils/RestApiClient'

export default {
  name: 'ts-sketch-metrics',
  props: ['sketch', 'sketchId', 'meta'],
  data () {
    return {
      count: 0
    }
  },
  mounted: function () {
    ApiClient.countSketchEvents(this.sketchId).then((response) => {
      this.count = response.data.meta.count
    }).catch((e) => {
      console.error(e)
    })
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss"></style>
