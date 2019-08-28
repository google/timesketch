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
  <nav class="navbar" role="navigation" aria-label="main navigation">
    <div class="navbar-item" v-if="currentAppContext === 'sketch'">
      <div class="tabs is-left">
        <ul>
          <li v-bind:class="{'is-active': currentPage === 'overview'}">
            <router-link :to="{ name: 'SketchOverview' }">
              <span class="icon is-small"><i class="fas fa-cubes" aria-hidden="true"></i></span>
              <span>Overview</span>
            </router-link>
          </li>
          <li v-bind:class="{'is-active': currentPage === 'explore'}">
            <router-link :to="{ name: 'SketchExplore' }">
              <span class="icon is-small"><i class="fas fa-search" aria-hidden="true"></i></span>
              <span>Explore</span>
            </router-link>
          </li>
          <li v-bind:class="{'is-active': currentPage === 'stories'}">
            <router-link :to="{ name: 'SketchStory' }">
              <span class="icon is-small"><i class="fas fa-book" aria-hidden="true"></i></span>
              <span>Stories</span>
            </router-link>
          </li>
        </ul>
      </div>
    </div>
    <div class="navbar-item" v-if="currentAppContext === 'explore'">
      <div class="tabs">
        <ul>
          <li v-bind:class="{'is-active': currentPage === 'search'}">
            <router-link :to="{ name: 'SketchExplore' }">
              <span>Search</span>
            </router-link>
          </li>
          <li v-bind:class="{'is-active': currentPage === 'aggregation'}">
            <router-link :to="{ name: 'SketchExploreAggregation' }">
              <span>Aggregations</span>
            </router-link>
          </li>
        </ul>
      </div>
    </div>
    <div class="navbar-end">
      <div class="navbar-item">
        <slot></slot>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'ts-navbar-secondary',
  props: ['currentAppContext', 'currentPage']
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
  .navbar {
    background: transparent;
  }
</style>
