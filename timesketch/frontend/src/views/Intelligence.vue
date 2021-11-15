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
    <ts-navbar-main>
      <template v-slot:left>
        {{ sketch.name }}
      </template>
    </ts-navbar-main>

    <ts-navbar-secondary currentAppContext="sketch" currentPage="intelligence"></ts-navbar-secondary>
    <section class="section">
      <ts-dynamic-table
        v-if="intelligence.data.length > 0"
        :data="intelligence.data"
        :section="intelligenceMeta"
        @table-delete="deleteIoc"
      >
      </ts-dynamic-table>
      <div v-else class="card-content">
        Examine events in the <router-link :to="{ name: 'Explore' }">Explore view</router-link> to add intelligence
        locally
      </div>
    </section>

  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import _ from 'lodash'

import TsDynamicTable from '../components/Common/TsDynamicTable'

export default {
  components: {
    TsDynamicTable,
  },
  data() {
    return {
      intelligenceMeta: {
        columns: [
          {
            field: 'ioc',
            label: 'IOC',
            searchable: true,
            type: 'text',
          },
          {
            field: 'type',
            label: 'Type',
            searchable: false,
            type: 'text',
          },
        ],
        key: 'local_intel',
        label: 'Local intelligence',
        deletable: true,
      },
    }
  },
  methods: {
    deleteIoc(ioc) {
      var data = this.intelligence.data.filter(i => i.ioc !== ioc.ioc)
      ApiClient.addSketchAttribute(this.sketch.id, 'intelligence', { data: data }, 'intelligence').then(() => {
        this.intelligence.data = data
      })
    },
    loadIntelligence() {
      ApiClient.getSketchAttributes(this.sketch.id).then(response => {
        if (!_.isEmpty(response.data.intelligence)) {
          this.meta.attributes.intelligence = response.data.intelligence
        }
      })
    },
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    intelligence() {
      if (this.meta.attributes.intelligence === undefined) {
        return { data: [] }
      }
      return this.meta.attributes.intelligence.value
    },
  },
  mounted() {
    this.loadIntelligence()
  },
}
</script>
