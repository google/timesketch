<!--
Copyright 2023 Google Inc. All rights reserved.

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
  <v-chip x-small @click="search(queryString)">
    {{ displayName }}
  </v-chip>
</template>

<script>
import EventBus from '../../main'

const defaultQueryFilter = () => {
  return {
    from: 0,
    terminate_after: 40,
    size: 40,
    indices: '_all',
    order: 'asc',
    chips: [],
  }
}

export default {
  props: ['searchchip'],
  computed: {
    displayName() {
      return this.searchchip.name || this.searchchip.description
    },
    queryString() {
      return this.searchchip.query_string || this.searchchip.value
    },
  },
  methods: {
    search(queryString) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = queryString
      eventData.queryFilter = defaultQueryFilter()
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
}
</script>
