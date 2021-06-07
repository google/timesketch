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
  <div class="card card-accent-background" style="margin-top:15px;">
    <header class="card-header">
      <p class="card-header-title">
        {{ messageTitle }} [<span v-for="timeline in timelines" :key="timeline">{{ timeline }}</span
        >]
      </p>
      <span class="card-header-icon" aria-label="close">
        <span class="delete" v-on:click="$emit('closeDetail')"></span>
      </span>
    </header>
    <div class="card-content">
      <table class="table is-fullwidth">
        <thead>
          <th></th>
          <th>Analyzer</th>
          <th>Result</th>
          <th>Timeline</th>
        </thead>
        <tbody>
          <tr v-for="(row, index) in tableData" :key="index">
            <td>
              <div
                style="width:10px; height: 10px; border-radius: 100%; margin-top:6px; margin-left:3px;"
                v-bind:class="{
                  pending: row.status === 'PENDING',
                  done: row.status === 'DONE',
                  started: row.status === 'STARTED',
                  error: row.status === 'ERROR',
                }"
              ></div>
            </td>
            <td>{{ row.analyzer }}</td>
            <td>{{ row.result }}</td>
            <td>{{ row.timeline.name }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  props: ['session'],
  data() {
    return {
      analysisSession: {},
      analyses: [],
      autoRefresh: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    totalAnalyzers() {
      return this.analyses.length
    },
    finishedAnalyzers() {
      let count = 0
      this.analyses.forEach(function(analyzer) {
        if (analyzer.status[0].status === 'DONE' || analyzer.status[0].status === 'ERROR') {
          count += 1
        }
      })
      return count
    },
    timelines() {
      let timelineSet = new Set()
      this.analyses.forEach(function(analyzer) {
        timelineSet.add(analyzer.timeline.name)
      })
      return timelineSet
    },
    tableData() {
      let tableArray = []
      this.analyses.forEach(function(analyzer) {
        let row = {}
        row.status = analyzer.status[0].status
        row.analyzer = analyzer.analyzer_name
        row.result = analyzer.result
        row.timeline = analyzer.timeline
        tableArray.push(row)
      })
      return tableArray
    },
    messageTitle() {
      return this.finishedAnalyzers + '/' + this.totalAnalyzers + ' analyzers done'
    },
  },
  methods: {
    fetchData() {
      ApiClient.getAnalyzerSession(this.sketch.id, this.session.id)
        .then(response => {
          this.analysisSession = response.data.objects[0]
          this.analyses = response.data.objects[0].analyses
          this.autoRefresh = true
        })
        .catch(e => {})
    },
  },
  beforeDestroy() {
    clearInterval(this.t)
    this.t = false
  },
  created() {
    this.analysisSession = this.session
    this.analyses = this.session.analyses
    this.autoRefresh = true
  },
  watch: {
    autoRefresh(val) {
      if (val && !this.t) {
        this.t = setInterval(
          function() {
            this.fetchData()
            if (this.finishedAnalyzers === this.totalAnalyzers) {
              this.autoRefresh = false
            }
          }.bind(this),
          5000
        )
      } else {
        clearInterval(this.t)
        this.t = false
      }
    },
  },
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.pending {
  background-color: orange;
}
.started {
  background-color: green;
  animation: blinker 1s linear infinite;
}
.done {
  background-color: green;
}
.error {
  background-color: red;
}

@keyframes blinker {
  50% {
    opacity: 0;
  }
}
</style>
