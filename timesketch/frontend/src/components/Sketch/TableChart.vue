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
  <div v-if="tableData">
    <b-table
      :data="tableData"
      :columns="getColumns()"
      :paginated="true"
      :pagination-simple="true"
      :per-page="10"
      :hoverable="true"
      icon-pack="fas"
      pagination-size="is-small">
    </b-table>
  </div>
</template>

<script>
export default {
  props: ['tableData'],
  methods: {
    getColumns: function () {
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
    }
  }
}

</script>
