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
  <section
    class="section"
    style="background-color:var(--navbar-background);padding:0;border-bottom: 1px solid var(--navbar-border-color);"
  >
    <div class="container is-fluid" style="padding-bottom:0;">
      <nav class="navbar" role="navigation" aria-label="main navigation">
        <div class="navbar-item" v-if="currentAppContext === 'sketch'">
          <div class="tabs is-left" v-if="activeTimelines.length">
            <ul>
              <li v-bind:class="{ 'is-active': currentPage === 'overview' }">
                <router-link :to="{ name: 'Overview' }">
                  <span class="icon is-small"><i class="fas fa-cubes" aria-hidden="true"></i></span>
                  <span>Overview</span>
                </router-link>
              </li>
              <li v-bind:class="{ 'is-active': currentPage === 'explore' }">
                <router-link :to="{ name: 'Explore' }" data-explore-element="true">
                  <span class="icon is-small"
                    ><i class="fas fa-search" data-explore-element="true" aria-hidden="true"></i
                  ></span>
                  <span data-explore-element="true">Explore</span>
                </router-link>
              </li>
              <li v-bind:class="{ 'is-active': currentPage === 'graph' }">
                <router-link :to="{ name: 'GraphOverview' }">
                  <span class="icon is-small"><i class="fas fa-project-diagram" aria-hidden="true"></i></span>
                  <span>Graph</span>
                </router-link>
              </li>
              <li v-bind:class="{ 'is-active': currentPage === 'aggregate' }">
                <router-link :to="{ name: 'Aggregate' }">
                  <span class="icon is-small"><i class="fas fa-chart-bar" aria-hidden="true"></i></span>
                  <span>Aggregate</span>
                </router-link>
              </li>
              <li v-bind:class="{ 'is-active': currentPage === 'analyzers' }">
                <router-link :to="{ name: 'Analyze' }">
                  <span class="icon is-small"><i class="fas fa-magic" aria-hidden="true"></i></span>
                  <span>Analyze</span>
                </router-link>
              </li>
              <li v-bind:class="{ 'is-active': currentPage === 'stories' }">
                <router-link :to="{ name: 'StoryOverview' }">
                  <span class="icon is-small"><i class="fas fa-book" aria-hidden="true"></i></span>
                  <span>Stories</span>
                </router-link>
              </li>
              <li v-bind:class="{ 'is-active': currentPage === 'sigma' }">
                <router-link :to="{ name: 'SigmaOverview' }">
                  <span class="icon is-small"><i class="fas fa-file-signature" aria-hidden="true"></i></span>
                  <span>Sigma</span>
                </router-link>
              </li>
              <li v-if="meta" v-bind:class="{ 'is-active': currentPage === 'attributes' }">
                <router-link :to="{ name: 'Attributes' }">
                  <span class="icon is-small"><i class="fas fa-table" aria-hidden="true"></i></span>
                  <span
                    >Attributes
                    <span
                      class="tag is-small"
                      style="background-color:var(--tag-background-color); color:var(--tag-font-color);"
                      >{{ attributeCount }}</span
                    >
                  </span>
                </router-link>
              </li>
              <li
                v-if="hasAttributeOntology('intelligence')"
                v-bind:class="{ 'is-active': currentPage === 'intelligence' }"
              >
                <router-link :to="{ name: 'Intelligence' }">
                  <span class="icon is-small"><i class="fas fa-brain" aria-hidden="true"></i></span>
                  <span
                    >Intelligence
                    <span
                      class="tag is-small"
                      style="background-color:var(--tag-background-color); color:var(--tag-font-color);"
                      >{{ attributeCount }}</span
                    >
                  </span>
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
    </div>
  </section>
</template>

<script>
export default {
  name: 'ts-navbar-secondary',
  props: {
    currentAppContext: String,
    currentPage: String,
  },
  methods: {
    hasAttributeOntology: function(ontologyName) {
      return Object.values(this.meta.attributes).some(value => value.ontology === ontologyName)
    },
  },
  computed: {
    meta() {
      return this.$store.state.meta
    },
    activeTimelines() {
      return this.$store.state.sketch.active_timelines
    },
    attributeCount() {
      return Object.entries(this.meta.attributes).length
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.navbar {
  background: transparent;
}
.tabs {
  margin-left: -20px;
}
.tabs a {
  padding: 0.5em 1em;
}
</style>
