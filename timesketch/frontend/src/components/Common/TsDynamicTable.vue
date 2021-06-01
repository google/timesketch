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
    <section class="section">
      <div class="container is-fluid">
        <div class="card" style="min-height:160px;">
          <header class="card-header">
            <p class="card-header-title">{{ section.label }}</p>
          </header>

          <div class="card-content">
            <b-table :data="data">
              <b-table-column
                v-for="column in section.columns"
                v-bind:key="column.field"
                :field="column.field"
                :label="column.label"
                v-slot="props"
                :numeric="typeof data[0][column.field] === 'number' ? true : false"
                sortable
              >
                <!-- column is an object -->
                <pre v-if="typeof props.row[column.field] === 'object'">{{ props.row[column.field] }}</pre>

                <!-- deal with all other cases -->
                <span v-else>{{ props.row[column.field] }}</span>
              </b-table-column>
            </b-table>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'TsDynamicTable',
  components: {},
  props: ['section', 'data'],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
}
</script>
