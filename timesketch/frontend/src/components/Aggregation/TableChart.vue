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
  <section>
    <div v-if="tableData.length">
      <b-field grouped group-multiline>
        <filterb-field label="Items per page">
        <b-input type="number" v-model="perPage"></b-input>
      </b-field>
      <b-field label="Filter">
        <b-input v-model="filter" type="text" placeholder="Search regexp">
        </b-input>
      </b-field>
      <b-field label="Filter Not">
        <b-input v-model="filternot" type="text" placeholder="Search regexp">
        </b-input>
      </b-field>
      <b-table
        :data="getData()"
        :columns="getColumns()"
        :paginated="true"
        :pagination-simple="true"
        :per-page="perPage"
        :filter="filter"
        :hoverable="true"
        icon-pack="fas"
        pagination-size="is-small"
      >
      </b-table>
    </div>
  </section>
</template>

<script>
export default {
  data() {
    return {
      perPage: 10,
      filter: null,
      filternot: null,
    }
  },
  props: ['tableData'],
  methods: {
    getData: function() {
      let datafilter = []
      let filterok = ''
      let filternot = ''
      if (this.filter != null) {
        filterok = this.filter
      }
      if (this.filternot != null) {
        filternot = this.filternot
      }
      this.tableData.forEach(function(item, array) {
        Object.keys(item).forEach(function(key) {
          if (key !== 'count' &&
            key !== 'duration' &&
            key !== 'last' &&
            key !== 'first' &&
            (new RegExp(filterok)).test(String(item[key]))) {
            if (filternot === '' ||
              !(new RegExp(filternot)).test(String(item[key]))) {
              datafilter.push(item)
            }
          }
        })
      })
      return datafilter
    },
    getColumns: function() {
      let columns = []
      let firstRow = this.tableData[0]
      Object.keys(firstRow).forEach(function(key) {
        columns.push({
          field: key,
          label: key,
          sortable: true,
        })
      })
      return columns
    },
  },
}
</script>
