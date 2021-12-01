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

    <ts-navbar-secondary currentAppContext="sketch" currentPage="analyzers"></ts-navbar-secondary>

    <!-- Analyzer logs -->
    <section class="section">
      <div class="container is-fluid">
        <ts-analyzer-history></ts-analyzer-history>
      </div>
    </section>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <p>Automatic analysis. Select timelines and analyzers in the lists below.</p>
            <br />
            <button
              :disabled="!analyzerCheckedRows.length || !timelineCheckedRows.length"
              class="button is-success"
              v-on:click="runAnalyzers"
            >
              Run {{ analyzerCheckedRows.length }} analyzers on {{ timelineCheckedRows.length }} timelines
            </button>
            <br />
            <br />
            <span v-for="session in sessions" :key="session.id">
              <ts-analysis-session-detail
                :session="session"
                @closeDetail="sessions.splice(sessions.indexOf(session), 1)"
              ></ts-analysis-session-detail>
            </span>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content" style="max-height: 500px; overflow-y: auto;">
            <span class="title is-6 is-uppercase">1. Select timelines to analyze</span>
            <br />
            <br />
            <b-table :data="timelines" :columns="timelineColumns" :checked-rows.sync="timelineCheckedRows" checkable>
            </b-table>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content">
            <span class="title is-6 is-uppercase">2. Select analyzers to run</span>
            <br />
            <br />
            <b-table
              :data="availableAnalyzers"
              :columns="analyzerColumns"
              :checked-rows.sync="analyzerCheckedRows"
              default-sort="display_name"
              checkable
            >
            </b-table>
          </div>
        </div>
      </div>
    </section>

    <br />
  </div>
</template>

<script>
import TsAnalyzerHistory from '../components/Analyze/AnalyzerHistory'
import TsAnalysisSessionDetail from '../components/Analyze/AnalyzerSessionDetail'
import ApiClient from '../utils/RestApiClient'

export default {
  props: ['sketchId'],
  components: {
    TsAnalyzerHistory,
    TsAnalysisSessionDetail,
  },
  data() {
    return {
      availableAnalyzers: [],
      timelineCheckedRows: [],
      analyzerCheckedRows: [],
      sessions: [],
      timelineColumns: [
        {
          field: 'name',
          label: 'Timeline',
        },
      ],
      analyzerColumns: [
        {
          field: 'display_name',
          label: 'Analyzer',
          sortable: true,
        },
        {
          field: 'description',
          label: 'Description',
        },
      ],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    timelines() {
      let t = []
      this.sketch.timelines.forEach(timeline => {
        t.push({
          id: timeline.id,
          name: timeline.name,
        })
      })
      return t
    },
  },
  methods: {
    runAnalyzers: function() {
      let timelineIds = this.timelineCheckedRows.map(timeline => timeline.id)
      let analyzerNames = this.analyzerCheckedRows.map(analyzer => analyzer.name)
      this.timelineCheckedRows = []
      this.analyzerCheckedRows = []
      ApiClient.runAnalyzers(this.sketch.id, timelineIds, analyzerNames)
        .then(response => {
          this.sessions = response.data.objects[0]
        })
        .catch(e => {})
    },
  },
  created: function() {
    ApiClient.getAnalyzers(this.sketch.id)
      .then(response => {
        this.availableAnalyzers = response.data
      })
      .catch(e => {
        console.error(e)
      })
  },
}
</script>
