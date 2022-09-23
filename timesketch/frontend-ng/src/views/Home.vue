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
  <v-container fluid pa-0>
    <div class="pa-5">
      <ts-sketch-list></ts-sketch-list>
    </div>
  </v-container>
</template>

<script>
import TsSketchList from '../components/SketchList'

export default {
  components: { TsSketchList },
  created: function () {
    this.$store.dispatch('resetState')
    document.title = 'Timesketch'
  },
}
</script>
<style lang="scss">
$toolbar-content-padding-x: 0;
</style>
