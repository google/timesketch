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
        <ts-navbar-secondary currentAppContext="sketch" currentPage="overview" :sketchId="sketch.id">
          <a class="button is-success is-rounded" style="margin-right:7px;" v-on:click="showModal = !showModal">
              <span class="icon is-small">
                <i class="fas fa-plus"></i>
              </span>
            <span>Timeline</span>
          </a>
          <a class="button is-link is-rounded" style="margin-right:10px;">
              <span class="icon is-small">
                <i class="fas fa-users"></i>
              </span>
            <span>Share</span>
          </a>
          <div class="dropdown is-hoverable is-right" v-bind:class="{'is-active': settingsDropdownActive}">
            <div class="dropdown-trigger">
              <a class="button" style="background:transparent;border:none;" aria-haspopup="true" aria-controls="dropdown-menu" v-on:click="settingsDropdownActive = !settingsDropdownActive">
                <span>More</span>
                <span class="icon is-small">
                <i class="fas fa-angle-down" aria-hidden="true"></i>
              </span>
              </a>
            </div>
            <div class="dropdown-menu" id="dropdown-menu" role="menu">
              <div class="dropdown-content">
                <a class="dropdown-item">
                <span class="icon is-small" style="margin-right:5px;">
                  <i class="fas fa-trash"></i>
                </span>
                  <span>Delete</span>
                </a>
                <hr class="dropdown-divider">
                <a class="dropdown-item">
                <span class="icon is-small" style="margin-right:5px;">
                  <i class="fas fa-edit"></i>
                </span>
                  <span>Edit</span>
                </a>
              </div>
            </div>
          </div>
        </ts-navbar-secondary>
      </div>
    </section>

    <!-- Title and description -->
    <section class="section">
      <div class="container" v-bind:class="{'is-fluid': fluid}">
        <div class="card">
          <div class="card-content">
            <ts-sketch-summary :sketch="sketch"></ts-sketch-summary>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats -->
    <section class="section">
      <div class="container" v-bind:class="{'is-fluid': fluid}">
        <div class="card">
          <div class="card-content">
            <ts-sketch-metrics :sketch="sketch" :sketchId="sketchId" :meta="meta"></ts-sketch-metrics>
          </div>
        </div>
      </div>
    </section>

    <!-- Timeline and View lists-->
    <section class="section">
      <div class="container" v-bind:class="{'is-fluid': fluid}">
        <div class="columns">
          <div class="column">
            <div class="card has-min-height">
              <header class="card-header">
                <p class="card-header-title">Timelines</p>
              </header>
              <div class="card-content" style="padding:5px;">
                <ts-timeline-list :timelines="sketch.timelines" :sketchId="sketch.id"></ts-timeline-list>
              </div>
            </div>
          </div>
          <div class="column">
            <div class="card has-min-height">
              <header class="card-header">
                <p class="card-header-title">Views</p>
              </header>
              <div class="card-content" style="padding:10px;">
                <ts-saved-view-list :views="meta.views"></ts-saved-view-list>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import ApiClient from '../../../utils/RestApiClient'
import TsSketchSummary from '../../../components/SketchSummary'
import TsSketchMetrics from '../../../components/SketchMetrics'
import TsTimelineList from '../../../components/SketchTimelineList'
import TsSavedViewList from '../../../components/SketchViewList'

export default {
  name: 'app',
  components: {
    TsSketchMetrics,
    TsSketchSummary,
    TsTimelineList,
    TsSavedViewList
  },
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
