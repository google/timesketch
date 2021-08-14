<!--
Copyright 2021 Google Inc. All rights reserved.

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
    <ts-navbar-main>
      <template v-slot:left>
        {{ sketch.name }}
      </template>
    </ts-navbar-main>

    <ts-navbar-secondary currentAppContext="sketch" currentPage="sigma"></ts-navbar-secondary>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <ts-sigma-list></ts-sigma-list>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import TsSigmaList from '../components/Sigma/SigmaList'

export default {
  props: ['sketchId'],
  components: { TsSigmaList },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
}
</script>
