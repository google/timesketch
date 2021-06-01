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

    <ts-navbar-secondary currentAppContext="sketch" currentPage="intelligence"></ts-navbar-secondary>

    <ts-dynamic-table
      v-for="section in intelligence.meta.sections"
      v-bind:key="section.key"
      :section="section"
      :data="intelligence.data[section.key]"
    >
    </ts-dynamic-table>
  </div>
</template>

<script>
import TsDynamicTable from '../components/Common/TsDynamicTable'

export default {
  components: {
    TsDynamicTable,
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    intelligence() {
      return this.meta.attributes.intelligence.value
    },
  },
}
</script>
