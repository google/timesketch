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
  <section class="section">
    <div class="container">
      <div class="card" style="min-height:160px;">
        <header class="card-header">
          <p class="card-header-title">Manage Saved Views</p>
        </header>
        <div class="card-content">
          <ts-saved-view-list :views="meta.views" :controls="true"></ts-saved-view-list>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import TsSavedViewList from './SketchViewsList'

export default {
  name: 'ts-sketch-views-manage',
  components: { TsSavedViewList },
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

<style lang="scss"></style>
