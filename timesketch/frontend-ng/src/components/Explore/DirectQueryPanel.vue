<!--
Copyright 2026 Google Inc. All rights reserved.

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
    <ts-direct-query-error v-if="error" :error="error" :language="language"></ts-direct-query-error>

    <template v-else>
      <v-progress-linear v-if="loading" indeterminate class="mb-2"></v-progress-linear>

      <!-- The previous result stays on screen, dimmed, while the next one is
           in flight. Swapping it for a bare progress bar loses the query the
           user is comparing against. -->
      <ts-direct-query-table
        v-if="result"
        :class="{ 'direct-query-stale': loading }"
        :columns="result.columns"
        :datarows="result.datarows"
        :total="result.total"
        :language="language"
        @export="exportResults"
      ></ts-direct-query-table>
    </template>

    <v-dialog v-model="showPlan" max-width="1000" scrollable>
      <v-card>
        <v-toolbar dense flat>
          <v-toolbar-title class="text-subtitle-2">
            {{ language.toUpperCase() }} execution plan
          </v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn small text @click="copyPlan">
            <v-icon left small>mdi-content-copy</v-icon>
            Copy
          </v-btn>
          <v-btn icon small @click="showPlan = false" title="Close">
            <v-icon small>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        <v-divider></v-divider>
        <v-card-text class="pt-3">
          <v-progress-linear v-if="explaining" indeterminate></v-progress-linear>
          <!-- The plan is the query as the engine resolved it, so it also
               shows the index and filters the backend added. -->
          <pre v-else class="direct-query-plan">{{ planText }}</pre>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient.js'
import TsDirectQueryTable from './DirectQueryTable.vue'
import TsDirectQueryError from './DirectQueryError.vue'

// Each language maps to its own set of endpoints, matching the backend split.
const API_METHODS = {
  ppl: { run: 'pplQuery', export: 'pplQueryExport', explain: 'pplQueryExplain' },
  sql: { run: 'sqlQuery', export: 'sqlQueryExport', explain: 'sqlQueryExplain' },
}

// Comfortably larger than the trailer the backend writes, so the last line is
// always whole within the slice.
const TRAILER_TAIL_BYTES = 16384

export default {
  name: 'TsDirectQueryPanel',
  components: {
    TsDirectQueryTable,
    TsDirectQueryError,
  },
  props: {
    // Mirrors ts-event-list: a new object identity triggers a new query.
    queryRequest: {
      type: Object,
      default: () => ({}),
    },
    language: {
      type: String,
      default: 'ppl',
      validator: (value) => Object.prototype.hasOwnProperty.call(API_METHODS, value),
    },
    // Carries the query to explain. A new object identity triggers a plan
    // lookup, the same way queryRequest triggers a run, so Explain works on
    // what is currently typed rather than on the last query that was run.
    explainRequest: {
      type: Object,
      default: () => ({}),
    },
    // Incremented by the parent to abort whatever is in flight.
    cancelToken: {
      type: Number,
      default: 0,
    },
  },
  data() {
    return {
      result: null,
      error: null,
      loading: false,
      controller: null,
      showPlan: false,
      explaining: false,
      planText: '',
    }
  },
  computed: {
    sketchId() {
      return this.$route.params.sketchId || this.$store.state.sketch.id
    },
  },
  watch: {
    queryRequest: {
      handler(newQueryRequest, oldQueryRequest) {
        // Return early if this isn't a new request.
        if (newQueryRequest === oldQueryRequest || !newQueryRequest) {
          return
        }
        this.search(newQueryRequest)
      },
    },
    language() {
      // Results from one language are meaningless under another.
      this.abort()
      this.reset()
    },
    explainRequest: {
      handler(newRequest, oldRequest) {
        if (newRequest === oldRequest || !newRequest || !newRequest.queryString) {
          return
        }
        this.explain(newRequest)
      },
    },
    cancelToken() {
      this.abort()
      this.loading = false
    },
    loading(value) {
      this.$emit('loading', value)
    },
  },
  methods: {
    reset() {
      this.result = null
      this.error = null
      this.loading = false
    },
    abort() {
      if (this.controller) {
        this.controller.abort()
        this.controller = null
      }
    },
    requestPayload(queryRequest) {
      const payload = {
        query: queryRequest.queryString,
        timeline_ids: queryRequest.timelineIds,
      }
      // Omitted rather than sent empty: the backend reads their absence as an
      // unbounded range.
      if (queryRequest.startTime) payload.start_time = queryRequest.startTime
      if (queryRequest.endTime) payload.end_time = queryRequest.endTime
      return payload
    },
    search(queryRequest) {
      const queryString = queryRequest && queryRequest.queryString
      if (!queryString || !queryString.trim()) {
        return
      }

      // The previous result is kept until this one lands so the table can stay
      // on screen while it runs.
      this.abort()
      this.error = null
      this.loading = true

      const controller = new AbortController()
      this.controller = controller

      ApiClient[API_METHODS[this.language].run](this.sketchId, this.requestPayload(queryRequest), {
        signal: controller.signal,
      })
        .then((response) => {
          const data = response.data
          if (data.error) {
            this.result = null
            this.error = data.error
          } else {
            this.result = data
          }
          this.loading = false
        })
        .catch((e) => {
          // A cancelled request is a deliberate act, not a failure; leave the
          // previous result in place.
          if (this.isCancellation(e)) {
            this.loading = false
            return
          }
          this.result = null
          this.error =
            e.response && e.response.data && e.response.data.message
              ? e.response.data.message
              : 'An unexpected error occurred.'
          this.loading = false
        })
    },
    isCancellation(e) {
      return Boolean(e) && (e.code === 'ERR_CANCELED' || e.name === 'CanceledError')
    },
    explain(queryRequest) {
      this.planText = ''
      this.explaining = true
      this.showPlan = true

      ApiClient[API_METHODS[this.language].explain](this.sketchId, this.requestPayload(queryRequest))
        .then((response) => {
          const data = response.data
          // The endpoint reports a rejected query in the envelope rather than
          // as an HTTP error, so the plan pane has to show it either way.
          this.planText = data.error
            ? this.formatPlanError(data.error)
            : JSON.stringify(data.plan, null, 2)
          this.explaining = false
        })
        .catch((e) => {
          const message =
            e.response && e.response.data && e.response.data.message ? e.response.data.message : e.message
          this.planText = message || 'Unable to retrieve the execution plan.'
          this.explaining = false
        })
    },
    formatPlanError(error) {
      return typeof error === 'string' ? error : JSON.stringify(error, null, 2)
    },
    copyPlan() {
      navigator.clipboard.writeText(this.planText).catch((e) => console.error(e))
    },
    exportResults() {
      ApiClient[API_METHODS[this.language].export](this.sketchId, this.requestPayload(this.queryRequest))
        .then(async (response) => {
          const blob = new Blob([response.data])
          this.downloadBlob(blob)
          // The export streams what it managed to read and records the shortfall
          // on the last line, so a truncated file arrives looking complete.
          const trailer = await this.readIncompleteTrailer(blob)
          if (trailer) {
            this.notifyIncompleteExport(trailer)
          }
        })
        .catch((e) => {
          const message =
            e.response && e.response.data && e.response.data.message ? e.response.data.message : e.message
          this.notify(`${this.language.toUpperCase()} export failed: ${message || 'unknown error'}`)
        })
    },
    downloadBlob(blob) {
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', this.exportFilename())
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    },
    exportFilename() {
      // Repeated exports of different queries would otherwise collide in the
      // download folder under one generic name.
      const stamp = new Date().toISOString().replace(/[:.]/g, '-')
      return `sketch${this.sketchId}_${this.language}_export_${stamp}.ndjson`
    },
    // Only the tail is read: an export can be far too large to pull into a
    // string, and the marker is always the final line.
    async readIncompleteTrailer(blob) {
      try {
        const tail = blob.slice(Math.max(0, blob.size - TRAILER_TAIL_BYTES))
        if (typeof tail.text !== 'function') return null
        const lines = (await tail.text()).trim().split('\n')
        const parsed = JSON.parse(lines[lines.length - 1])
        return parsed && parsed.incomplete ? parsed : null
      } catch (e) {
        // A complete export ends with a data row, which will not parse as a
        // trailer. That is the normal path, not a failure.
        return null
      }
    },
    notifyIncompleteExport(trailer) {
      const rows = typeof trailer.rows_returned === 'number' ? trailer.rows_returned.toLocaleString() : 'some'
      const detail = trailer.detail ? ` ${trailer.detail}` : ''
      this.notify(`${this.language.toUpperCase()} export is incomplete: it stopped after ${rows} rows.${detail}`)
    },
    notify(message) {
      // No timeout: a short download looks like a good one, so the warning has
      // to outlast a glance at the screen.
      this.$store.dispatch('setSnackBar', { message, color: 'error', timeout: -1 })
    },
  },
  created() {
    if (Object.keys(this.queryRequest).length) {
      this.search(this.queryRequest)
    }
  },
  beforeDestroy() {
    this.abort()
  },
}
</script>

<style scoped>
.direct-query-stale {
  opacity: 0.45;
  transition: opacity 0.15s ease-in-out;
  pointer-events: none;
}

.direct-query-plan {
  font-family: 'Roboto Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.8em;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  margin: 0;
}
</style>
