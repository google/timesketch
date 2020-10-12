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
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'app',
  created: function () {
    let element = document.body
    if (!localStorage.theme) {
      localStorage.theme = 'light'
    }
    element.dataset.theme = localStorage.theme
  }
}
</script>

<style src="vue-multiselect/dist/vue-multiselect.min.css"></style>
<style lang="scss"></style>
