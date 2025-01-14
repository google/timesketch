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
  <div>
    <v-chip v-if="type === 'chip'" small @click="search(queryString)">
      <v-icon class="mr-1" small>mdi-magnify</v-icon>
      {{ displayName }}
    </v-chip>
    <div v-if="type === 'link'" @click="search(queryString)" :class="!searchchip.error ? 'enabled' : ''">
      <div style="font-size: 0.9em" class="pb-1 pl-1" :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'">
        <span>
          <v-icon small class="mr-2 ml-2">{{ icon }}</v-icon>
          <strong>{{ displayName }}</strong>
          <br />
          <small v-if="searchchip.error" class="ml-8" style="font-size: 0.8em">{{ searchchip.error }}</small>
          <div v-else style="width: 90%" class="truncate-with-ellipsis">
            <small class="ml-8" style="font-size: 0.8em">{{ queryString }}</small>
          </div>
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import EventBus from '../../event-bus.js'

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
  props: ['searchchip', 'type', 'icon'],
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
      if (this.searchchip.error) {
        return
      }
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = queryString
      eventData.queryFilter = defaultQueryFilter()
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
}
</script>

<style scoped lang="scss">
.truncate-with-ellipsis {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.enabled {
  cursor: pointer;
}
</style>
