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
  <v-card outlined>
    <v-toolbar dense flat>
      <v-toolbar-title class="text-subtitle-2 d-flex align-center">
        <v-chip small class="mr-2">{{ language.toUpperCase() }}</v-chip>
        <span v-if="capped">
          Showing the first {{ shownCount }} of {{ totalCount }} matching rows
          <v-icon small class="ml-1" :title="cappedHint">mdi-information-outline</v-icon>
        </span>
        <span v-else>{{ shownCount }} {{ datarows.length === 1 ? 'row' : 'rows' }}</span>
      </v-toolbar-title>
      <v-spacer></v-spacer>

      <v-btn icon small :color="wrapText ? 'primary' : ''" @click="wrapText = !wrapText" :title="wrapTitle">
        <v-icon small>{{ wrapText ? 'mdi-wrap-disabled' : 'mdi-wrap' }}</v-icon>
      </v-btn>

      <v-menu offset-y :close-on-content-click="false" max-height="400">
        <template v-slot:activator="{ on, attrs }">
          <v-btn icon small v-bind="attrs" v-on="on" title="Show or hide columns">
            <v-icon small>mdi-table-column</v-icon>
          </v-btn>
        </template>
        <v-list dense>
          <v-list-item @click="showAllColumns" :disabled="!hiddenColumns.length">
            <v-list-item-title class="text-caption">Show all columns</v-list-item-title>
          </v-list-item>
          <v-divider></v-divider>
          <v-list-item v-for="(col, index) in columns" :key="index" @click="toggleColumn(index)">
            <v-list-item-action class="mr-2">
              <v-simple-checkbox
                :value="!isHidden(index)"
                :ripple="false"
                dense
                @click="toggleColumn(index)"
              ></v-simple-checkbox>
            </v-list-item-action>
            <v-list-item-title class="text-caption">{{ col }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

      <v-btn small text @click="copyAsCsv" title="Copy the returned rows as CSV">
        <v-icon left small>mdi-content-copy</v-icon>
        Copy CSV
      </v-btn>
      <v-btn small text @click="$emit('export')" title="Export the full result set">
        <v-icon left small>mdi-download</v-icon>
        Export All
      </v-btn>
    </v-toolbar>
    <v-divider></v-divider>

    <v-data-table
      :headers="tableHeaders"
      :items="tableRows"
      :items-per-page="25"
      :footer-props="footerProps"
      :height="tableHeight"
      fixed-header
      dense
      class="direct-query-table"
    >
      <template v-slot:item="{ item }">
        <tr>
          <td class="direct-query-expand">
            <v-btn icon x-small @click="openRow(item)" title="Show the full row">
              <v-icon small>mdi-arrow-expand</v-icon>
            </v-btn>
          </td>
          <!-- Keyed by position: a result set may repeat a column name (a join,
               or two identically named aggregates), which would collide in a
               name-keyed row object and duplicate the Vue list key. -->
          <td v-for="index in visibleIndexes" :key="index">
            <div class="direct-query-cell-row" :class="{ 'justify-end': isNumeric(index) }">
              <!-- The clamp lives on an inner block box on purpose. A td in an
                   auto-layout table takes its minimum width from its content, so
                   a max-width there is overridden by a long unbroken value and
                   the column stretches instead of ellipsizing. -->
              <div
                class="direct-query-cell"
                :class="wrapText ? 'direct-query-cell--wrap' : 'direct-query-cell--truncate'"
                :title="wrapText ? '' : cellValue(item, index)"
              >
                {{ cellValue(item, index) }}
              </div>
              <v-btn
                v-if="canPivot(item, index)"
                class="direct-query-pivot ml-1"
                icon
                x-small
                @click.stop="pivot(item, index)"
                :title="pivotTitle(item, index)"
              >
                <v-icon x-small>mdi-filter-plus-outline</v-icon>
              </v-btn>
            </div>
          </td>
        </tr>
      </template>
    </v-data-table>

    <v-dialog v-model="showRowDetail" max-width="900" scrollable>
      <v-card v-if="selectedRow">
        <v-toolbar dense flat>
          <v-toolbar-title class="text-subtitle-2">Row detail</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn small text @click="copyRowAsJson">
            <v-icon left small>mdi-content-copy</v-icon>
            Copy JSON
          </v-btn>
          <v-btn icon small @click="showRowDetail = false" title="Close">
            <v-icon small>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        <v-divider></v-divider>
        <v-card-text class="pa-0">
          <v-simple-table dense>
            <tbody>
              <tr v-for="(col, index) in columns" :key="index">
                <td class="direct-query-detail-key">{{ col }}</td>
                <td class="direct-query-detail-value">{{ formatCell(selectedRow[index]) }}</td>
              </tr>
            </tbody>
          </v-simple-table>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script>
import EventBus from '../../event-bus.js'

// Scanning every row to decide alignment is wasted work on a large result;
// the leading rows settle it in practice.
const NUMERIC_SAMPLE_ROWS = 200

// A pivot turns a column name into a Lucene term filter, so it only makes
// sense for columns that name a real field. An aggregate alias such as
// "count()" or "span(datetime,1h)" is not a field and would filter on nothing.
const FIELD_NAME = /^[A-Za-z_][A-Za-z0-9_.@-]*$/

const PIVOT_TITLE_MAX = 60

// A term chip matches against <field>.keyword, and Timesketch maps keyword
// sub-fields with ignore_above: 256. A longer value was never indexed there, so
// the pivot would return no events and look broken rather than empty.
const KEYWORD_IGNORE_ABOVE = 256

export default {
  name: 'TsDirectQueryTable',
  props: {
    columns: {
      type: Array,
      required: true,
    },
    datarows: {
      type: Array,
      required: true,
    },
    total: {
      type: Number,
      default: 0,
    },
    language: {
      type: String,
      default: 'ppl',
    },
  },
  data() {
    return {
      wrapText: false,
      hiddenColumns: [],
      showRowDetail: false,
      selectedRowIndex: null,
      // "loaded" distinguishes the footer's page counter from the toolbar's
      // count of rows matched by the query.
      footerProps: {
        'items-per-page-options': [10, 25, 50, 100],
        pageText: '{0}-{1} of {2} loaded',
      },
    }
  },
  computed: {
    visibleIndexes() {
      return this.columns.map((col, index) => index).filter((index) => !this.isHidden(index))
    },
    tableHeaders() {
      const headers = this.visibleIndexes.map((index) => ({
        text: this.columns[index],
        value: String(index),
        sortable: true,
        align: this.isNumeric(index) ? 'end' : 'start',
      }))
      // Leading cell for the row-detail button.
      return [{ text: '', value: 'expand', sortable: false, width: '1%' }, ...headers]
    },
    tableRows() {
      return this.datarows.map((row, rowIndex) => {
        // Numeric keys cannot collide with this one, and it survives sorting
        // so the detail dialog can find the original row.
        const obj = { __rowIndex: rowIndex }
        this.columns.forEach((col, index) => {
          obj[index] = row[index]
        })
        return obj
      })
    },
    numericColumns() {
      const sample = this.datarows.slice(0, NUMERIC_SAMPLE_ROWS)
      return this.columns.map((col, index) => {
        let sawValue = false
        for (const row of sample) {
          const value = row[index]
          if (value === null || value === undefined || value === '') continue
          if (typeof value !== 'number') return false
          sawValue = true
        }
        return sawValue
      })
    },
    tableHeight() {
      // Sticky headers need a bounded height, but a short result should not sit
      // in a tall empty box.
      return this.datarows.length > 10 ? '60vh' : undefined
    },
    selectedRow() {
      return this.selectedRowIndex === null ? null : this.datarows[this.selectedRowIndex]
    },
    capped() {
      return this.total > this.datarows.length
    },
    shownCount() {
      return this.datarows.length.toLocaleString()
    },
    totalCount() {
      return this.total.toLocaleString()
    },
    cappedHint() {
      return (
        'The query matched more rows than were returned. Use Export All for the ' +
        'complete result set, or narrow the query.'
      )
    },
    wrapTitle() {
      return this.wrapText ? 'Truncate long values' : 'Wrap long values'
    },
  },
  watch: {
    columns() {
      this.hiddenColumns = []
      this.showRowDetail = false
      this.selectedRowIndex = null
    },
  },
  methods: {
    // Shared by the cell, its tooltip, the detail dialog and the CSV copy so
    // they all agree. Vue interpolates an object as pretty-printed JSON, which
    // String() would render as [object Object] in the tooltip.
    formatCell(value) {
      if (value === null || value === undefined) return ''
      if (typeof value === 'object') return JSON.stringify(value)
      return String(value)
    },
    cellValue(item, index) {
      return this.formatCell(item[index])
    },
    isNumeric(index) {
      return Boolean(this.numericColumns[index])
    },
    isHidden(index) {
      return this.hiddenColumns.indexOf(index) !== -1
    },
    toggleColumn(index) {
      if (this.isHidden(index)) {
        this.hiddenColumns = this.hiddenColumns.filter((hidden) => hidden !== index)
      } else if (this.visibleIndexes.length > 1) {
        // Hiding the last column would leave an unreadable table.
        this.hiddenColumns = [...this.hiddenColumns, index]
      }
    },
    showAllColumns() {
      this.hiddenColumns = []
    },
    openRow(item) {
      this.selectedRowIndex = item.__rowIndex
      this.showRowDetail = true
    },
    // A count or an average identifies no evidence, and neither does a blank,
    // so the pivot is only offered where the resulting filter would mean
    // something.
    canPivot(item, index) {
      if (this.isNumeric(index)) return false
      if (!FIELD_NAME.test(String(this.columns[index]))) return false
      const value = this.cellValue(item, index)
      return value !== '' && value !== 'null' && value.length <= KEYWORD_IGNORE_ABOVE
    },
    pivotTitle(item, index) {
      const value = this.cellValue(item, index)
      const shown = value.length > PIVOT_TITLE_MAX ? value.slice(0, PIVOT_TITLE_MAX) + '...' : value
      return 'Show the events where ' + this.columns[index] + ' is ' + shown
    },
    // Same contract the chart components use to hand a value to the event
    // list: Explore owns the switch back to Lucene and the search itself.
    pivot(item, index) {
      EventBus.$emit('setQueryAndFilter', {
        doSearch: true,
        chip: {
          field: this.columns[index],
          value: this.cellValue(item, index),
          type: 'term',
          operator: 'must',
          active: true,
        },
      })
    },
    copyRowAsJson() {
      if (!this.selectedRow) return
      const obj = {}
      this.columns.forEach((col, index) => {
        obj[col] = this.selectedRow[index]
      })
      this.copyToClipboard(JSON.stringify(obj, null, 2))
    },
    csvEscape(value) {
      return value.includes(',') || value.includes('"') || value.includes('\n')
        ? '"' + value.replace(/"/g, '""') + '"'
        : value
    },
    copyAsCsv() {
      const indexes = this.visibleIndexes
      const header = indexes.map((index) => this.csvEscape(String(this.columns[index]))).join(',')
      const rows = this.datarows.map((row) =>
        indexes.map((index) => this.csvEscape(this.formatCell(row[index]))).join(',')
      )
      this.copyToClipboard([header, ...rows].join('\n'))
    },
    copyToClipboard(text) {
      navigator.clipboard.writeText(text).catch((e) => console.error(e))
    },
  },
}
</script>

<style scoped>
.direct-query-table {
  font-size: 0.85em;
}

.direct-query-expand {
  width: 1%;
  white-space: nowrap;
}

.direct-query-cell-row {
  display: flex;
  align-items: center;
}

.direct-query-cell {
  max-width: 400px;
}

/* Kept out of the way until the row is under the pointer, so a dense result
   does not turn into a wall of buttons. Focus keeps it reachable by keyboard. */
.direct-query-pivot {
  opacity: 0;
  transition: opacity 0.1s;
}

tr:hover .direct-query-pivot,
.direct-query-pivot:focus {
  opacity: 1;
}

.direct-query-cell--truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.direct-query-cell--wrap {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.direct-query-detail-key {
  width: 220px;
  vertical-align: top;
  font-weight: 500;
  white-space: nowrap;
}

.direct-query-detail-value {
  font-family: 'Roboto Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.85em;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
</style>
