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
  <b-message :title="messageTitle" :closable="false" style="margin-top:15px;">
    <table class="table is-fullwidth">
      <colgroup>
        <col span="1" style="width: 5%;">
        <col span="1" style="width: 15%;">
        <col span="1" style="width: 80%;">
      </colgroup>
      <tbody>
      <tr v-for="row in tableData">
        <td>{{row.status}}</td>
        <td>{{row.analyzer}}</td>
        <td>{{row.result}}</td>
      </tr>
      </tbody>
    </table>
  </b-message>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  props: ['timeline', 'sessionId'],
  data () {
    return {
      analysisSession: {},
      analyses: [],
      autoRefresh: false,
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    totalAnalyzers () {
      return this.analyses.length
    },
    finishedAnalyzers () {
      let count = 0
      this.analyses.forEach(function (analyzer) {
        if (analyzer.status[0].status === 'DONE' || analyzer.status[0].status === 'ERROR') {
          count += 1
        }
      })
      return count
    },
    runningAnalyzer () {
      let running = false
      this.analyses.forEach(function (analyzer) {
        if (analyzer.status[0].status === 'STARTED') {
          running = analyzer.analyzer_name
        }
      })
      return running
    },
    tableData () {
      let tableArray = []
      this.analyses.forEach(function (analyzer) {
        let row = {}
        row.status = analyzer.status[0].status
        row.analyzer = analyzer.analyzer_name
        row.result = analyzer.result
        tableArray.push(row)
      })
      return tableArray
    },
    messageTitle () {
      return this.finishedAnalyzers + '/' + this.totalAnalyzers + ' analyzers done'
    }
  },
  methods: {
    fetchData () {
      if (!this.sessionId) {
        return
      }
      ApiClient.getAnalyzerSession(this.sketch.id, this.sessionId).then((response) => {
        this.analysisSession = response.data.objects[0]
        this.analyses = response.data.objects[0].analyses
        this.autoRefresh = true
      }).catch((e) => {})
    }
  },
  watch: {
    autoRefresh(val) {
      if (val && !this.t) {
        this.t = setInterval(function () {
          this.fetchData()
          if (this.finishedAnalyzers === this.totalAnalyzers) {
            this.autoRefresh = false
            this.$emit('sessionDone')
          }
        }.bind(this), 3000)}
      else {
        clearInterval(this.t)
        this.t = false
      }
    },
    sessionId(val) {
      if (val) {
        this.fetchData()
      }
    }
  }
}
</script>
