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
  <div id="app">
    <ts-navbar-main></ts-navbar-main>
    <section class="section">
      <div class="container" v-bind:class="{'is-fluid': fluid}">
        <ts-navbar-secondary currentAppContext="sketch" currentPage="explore" :sketchId="sketch.id"></ts-navbar-secondary>
      </div>
    </section>

    <!-- Placeholder -->
    <section class="section">
      <div class="container" v-bind:class="{'is-fluid': fluid}">
        <div class="card">
          <div class="card-content">
            <span>Work in progress..</span>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import ApiClient from '../../../utils/RestApiClient'

export default {
  name: 'app',
  components: {},
  props: ['sketchId'],
  data () {
    return {
      sketch: {},
      meta: {}
    }
  },
  mounted: function () {
    ApiClient.getSketch(this.sketchId).then((response) => {
      this.sketch = response.data.objects[0]
      this.meta = response.data.meta
    }).catch((e) => {})
  }
}
</script>

<style lang="scss">
  .has-min-height {
    min-height: 300px;
  }
</style>
