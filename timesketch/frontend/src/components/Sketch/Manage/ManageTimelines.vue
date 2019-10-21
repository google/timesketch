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
    <section class="section">
      <div class="container is-fluid">
        <ts-navbar-secondary currentAppContext="sketch" currentPage=""></ts-navbar-secondary>
      </div>
    </section>
    <ts-sketch-timelines-manage></ts-sketch-timelines-manage>
  </div>
</template>

<script>
import TsSketchTimelinesManage from './TimelinesManage'

export default {
  name: 'ts-sketch-timelines',
  components: { TsSketchTimelinesManage }
}
</script>

<style lang="scss"></style>
