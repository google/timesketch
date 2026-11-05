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
  <div class="direct-query-editor pa-2">
    <v-textarea
      :value="value"
      @input="$emit('input', $event)"
      :placeholder="placeholder"
      auto-grow
      rows="1"
      row-height="22"
      hide-details
      dense
      flat
      solo
      autocomplete="off"
      spellcheck="false"
      ref="editor"
      @keydown.ctrl.enter.prevent="run"
      @keydown.meta.enter.prevent="run"
    ></v-textarea>

    <div v-if="findings.length" class="mt-1">
      <div v-for="(item, index) in findings" :key="index" class="d-flex align-start text-caption mb-1">
        <v-icon x-small :color="item.severity === 'error' ? 'error' : 'warning'" class="mr-1 mt-1">
          {{ item.severity === 'error' ? 'mdi-alert-circle-outline' : 'mdi-alert-outline' }}
        </v-icon>
        <span><strong>{{ item.message }}</strong> {{ item.hint }}</span>
      </div>
    </div>

    <div class="d-flex align-center flex-wrap mt-1">
      <v-menu v-model="timeMenu" offset-y :close-on-content-click="false" max-width="340">
        <template v-slot:activator="{ on, attrs }">
          <v-btn small text v-bind="attrs" v-on="on" :color="hasTimeRange ? 'primary' : ''">
            <v-icon left small>mdi-clock-outline</v-icon>
            {{ timeRangeLabel }}
          </v-btn>
        </template>
        <v-card>
          <v-list dense>
            <v-list-item v-for="preset in presets" :key="preset.label" @click="applyPreset(preset)">
              <v-list-item-title class="text-caption">{{ preset.label }}</v-list-item-title>
            </v-list-item>
          </v-list>
          <v-divider></v-divider>
          <v-card-text class="pt-3">
            <v-text-field
              :value="startTime"
              @input="emitRange($event, endTime)"
              type="datetime-local"
              label="From (UTC)"
              dense
              outlined
              hide-details
              class="mb-3"
            ></v-text-field>
            <v-text-field
              :value="endTime"
              @input="emitRange(startTime, $event)"
              type="datetime-local"
              label="To (UTC)"
              dense
              outlined
              hide-details
            ></v-text-field>
            <!-- The bound is applied to the numeric `timestamp` field rather
                 than `datetime`, which is the only form that behaves
                 consistently across both plugins. -->
            <div class="text-caption text--secondary mt-2">
              Applied to every query as a bound on the event timestamp.
            </div>
          </v-card-text>
          <v-card-actions>
            <v-btn small text :disabled="!hasTimeRange" @click="clearRange">Clear</v-btn>
            <v-spacer></v-spacer>
            <v-btn small text @click="timeMenu = false">Done</v-btn>
          </v-card-actions>
        </v-card>
      </v-menu>

      <span class="text-caption text--secondary ml-2">
        {{ language.toUpperCase() }} &mdash; press {{ runShortcut }} to run, Enter for a new line
      </span>
      <span v-if="timelineCount" class="text-caption text--secondary ml-3">
        <v-icon x-small class="mr-1">mdi-file-tree</v-icon>
        Scoped to {{ timelineCount }} {{ timelineCount === 1 ? 'timeline' : 'timelines' }}
      </span>

      <v-spacer></v-spacer>

      <v-btn small text @click="$emit('help')" title="Show query examples">
        <v-icon left small>mdi-help-circle-outline</v-icon>
        Examples
      </v-btn>
      <v-btn small text :disabled="!hasQuery || running" @click="$emit('explain')" title="Show the execution plan without running the query">
        <v-icon left small>mdi-sitemap-outline</v-icon>
        Explain
      </v-btn>
      <v-btn v-if="running" small depressed color="error" class="ml-2" @click="$emit('cancel')">
        <v-icon left small>mdi-close</v-icon>
        Cancel
      </v-btn>
      <v-btn v-else small depressed color="primary" class="ml-2" :disabled="!hasQuery" @click="run">
        <v-icon left small>mdi-play</v-icon>
        Run
      </v-btn>
    </div>
  </div>
</template>

<script>
import { lintDirectQuery } from '../../utils/DirectQueryLint.js'

const PLACEHOLDERS = {
  ppl: 'stats count() as cnt by data_type | sort - cnt | head 10',
  sql: 'SELECT data_type, COUNT(*) AS cnt GROUP BY data_type ORDER BY cnt DESC LIMIT 10',
}

const PRESETS = [
  { label: 'All time', hours: null },
  { label: 'Last 24 hours', hours: 24 },
  { label: 'Last 7 days', hours: 24 * 7 },
  { label: 'Last 30 days', hours: 24 * 30 },
]

// `datetime-local` inputs speak "YYYY-MM-DDTHH:mm" with no zone. Everything
// here is built and read as UTC, matching the label on the fields, so a
// timeline is not shifted by wherever the analyst happens to be sitting.
function toInputValue(date) {
  return date.toISOString().slice(0, 16)
}

export default {
  name: 'TsDirectQueryEditor',
  props: {
    value: {
      type: String,
      default: '',
    },
    language: {
      type: String,
      default: 'ppl',
    },
    running: {
      type: Boolean,
      default: false,
    },
    timelineCount: {
      type: Number,
      default: 0,
    },
    startTime: {
      type: String,
      default: '',
    },
    endTime: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      timeMenu: false,
      presets: PRESETS,
    }
  },
  computed: {
    placeholder() {
      return PLACEHOLDERS[this.language] || ''
    },
    hasQuery() {
      return Boolean(this.value && this.value.trim())
    },
    findings() {
      return lintDirectQuery(this.language, this.value)
    },
    hasTimeRange() {
      return Boolean(this.startTime || this.endTime)
    },
    timeRangeLabel() {
      if (!this.hasTimeRange) return 'All time'
      if (!this.endTime) return `From ${this.startTime.replace('T', ' ')}`
      if (!this.startTime) return `Until ${this.endTime.replace('T', ' ')}`
      return `${this.startTime.replace('T', ' ')} to ${this.endTime.replace('T', ' ')}`
    },
    runShortcut() {
      return this.isMac ? '\u2318 Enter' : 'Ctrl+Enter'
    },
    isMac() {
      return typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)
    },
  },
  methods: {
    run() {
      if (this.hasQuery && !this.running) {
        this.$emit('run')
      }
    },
    emitRange(start, end) {
      this.$emit('update:timeRange', { start: start || '', end: end || '' })
    },
    applyPreset(preset) {
      if (!preset.hours) {
        this.clearRange()
      } else {
        const now = new Date()
        this.emitRange(toInputValue(new Date(now.getTime() - preset.hours * 3600 * 1000)), toInputValue(now))
      }
      this.timeMenu = false
    },
    clearRange() {
      this.emitRange('', '')
    },
    focus() {
      if (this.$refs.editor) {
        this.$refs.editor.focus()
      }
    },
  },
}
</script>

<style scoped>
.direct-query-editor {
  width: 100%;
  min-width: 0;
}

/* A pipeline or a SELECT is read column-wise; the proportional UI font makes
   operators and quoting hard to scan. */
.direct-query-editor ::v-deep textarea {
  font-family: 'Roboto Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.9em;
  line-height: 1.45;
}
</style>
