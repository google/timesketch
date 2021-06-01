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
    <span v-if="manualTrigger">Starting analyzers..</span>
    <b-progress
      v-if="taskCounters.total_sessions"
      :value="taskCounters.tasks['DONE'] + taskCounters.tasks['ERROR']"
      size="is-medium"
      :max="taskCounters.total_tasks"
      type="is-info"
      show-value
    >
      {{ taskCounters.tasks['DONE'] + taskCounters.tasks['ERROR'] }} out of {{ taskCounters.total_tasks }}
    </b-progress>
    <span v-for="sessionId in sessionIds" :key="sessionId">
      <ts-analysis-session-detail
        :session-id="sessionId"
        @closeDetail="sessionIds.splice(sessionIds.indexOf(sessionId), 1)"
      ></ts-analysis-session-detail>
    </span>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsAnalysisSessionDetail from './AnalyzerSessionDetail'
import EventBus from '../../main'

export default {
  components: { TsAnalysisSessionDetail },
  data() {
    return {
      taskCounters: {
        tasks: {},
        total_sessions: 0,
        total_tasks: 0,
      },
      autoRefresh: false,
      sessionIds: [],
      manualTrigger: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  methods: {
    fetchData() {
      ApiClient.getActiveAnalyzerSessions(this.sketch.id)
        .then(response => {
          let taskCounters = response.data['objects'][0]
          this.taskCounters = taskCounters
          taskCounters.sessions.forEach(sessionId => {
            if (this.sessionIds.indexOf(sessionId) === -1) this.sessionIds.push(sessionId)
          })
          this.manualTrigger = false
        })
        .catch(e => {
          console.error(e)
        })
    },
    triggerAnalysis() {
      this.manualTrigger = true
      this.fetchData()
    },
  },
  created() {
    EventBus.$on('triggerAnalysis', this.triggerAnalysis)
    this.fetchData()
    this.autoRefresh = true
  },
  beforeDestroy() {
    EventBus.$off('triggerAnalysis', this.triggerAnalysis)
    clearInterval(this.t)
    this.t = false
  },
  watch: {
    autoRefresh(val) {
      if (val && !this.t) {
        this.t = setInterval(
          function() {
            this.fetchData()
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
<style scoped lang="scss"></style>
