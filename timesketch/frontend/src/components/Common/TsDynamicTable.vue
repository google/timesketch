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
          <div class="card-content ts-dynamic-table" v-if="dataArray.length > 0">
            <b-table :data="dataArray">
              <b-table-column
                v-for="column in section.columns"
                v-bind:key="column.field"
                :field="column.field"
                :label="column.label"
                v-slot="props"
                :numeric="typeof dataArray[0][column.field] === 'number' ? true : false"
                sortable
              >
                <!-- column is an text -->
                <div v-if="column.type === 'text'">
                  <router-link
                    v-if="column.searchable"
                    :to="{ name: 'Explore', query: generateQuery(props.row[column.field], column) }"
                  >
                    {{ props.row[column.field] }}
                    <i class="fas fa-search" aria-hidden="true"></i>
                  </router-link>
                  <span v-else>{{ props.row[column.field] }}</span>
                </div>

                <!-- column is a timestamp -->
                <div v-else-if="column.type === 'timestamp'">
                  {{ props.row[column.field] }}
                </div>

                <!-- column is a list of tags -->
                <div v-else-if="column.type === 'list'">
                  <b-taglist v-if="column.searchable">
                    <router-link
                      v-bind:key="tag"
                      v-for="tag in props.row[column.field]"
                      :to="{ name: 'Explore', query: generateQuery(tag, column) }"
                    >
                      <b-tag type="is-link is-light">{{ tag }} <i class="fas fa-search" aria-hidden="true"></i></b-tag>
                    </router-link>
                  </b-taglist>
                  <b-taglist v-else>
                    <b-tag v-bind:key="tag" v-for="tag in props.row[column.field]" type="is-light">{{ tag }}</b-tag>
                  </b-taglist>
                </div>

                <!-- column is an object -->
                <pre v-else-if="column.type === 'object'">{{ props.row[column.field] }}</pre>

                <!-- deal with all other cases -->
                <div v-else>{{ props.row[column.field] }}</div>
              </b-table-column>
              <b-table-column v-if="section.deletable" label="Delete" v-slot="props">
                <span
                  class="icon is-small"
                  style="cursor:pointer;"
                  title="Apply 'Exclude' filter"
                  @click="$emit('table-delete', props.row)"
                  ><i class="fas fa-trash"></i
                ></span>
              </b-table-column>
            </b-table>
          </div>
          <div class="card-content" v-else>Empty table</div>
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
    dataArray() {
      return Object.values(this.data)
    },
  },
  methods: {
    generateQuery(value, column) {
      let query = `"${value}"`
      if (column.searchKey) {
        query = `${column.searchKey}:${query}`
      }
      return { q: query }
    },
  },
}
</script>

<style scoped lang="scss">
.tags a:not(:last-child) {
  margin-right: 0.5rem;
}

.ts-dynamic-table a {
  color: var(--default-link-color);
}
</style>
