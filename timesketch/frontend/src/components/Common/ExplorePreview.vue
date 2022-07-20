<!--
Copyright 2022 Google Inc. All rights reserved.

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
  <span v-if="previewData.length" @mouseenter="delayDisplay(true, 0)" @mouseleave="delayDisplay(false, 500)">
    <b-tag rounded type="is-success is-light">
      <span class="icon is-medium"><i class="fas fa-eye" aria-hidden="true"></i></span>
      {{ previewData.length }}
    </b-tag>
    <div class="preview-box" v-show="isOpen">
      <div class="preview-title">
        Previewing results for <code>{{ searchQuery['q'] }}</code>
      </div>
      <event-list
        :eventList="previewData"
        order="asc"
        :displayOptions="{ showEmojis: false, showMillis: false, showTags: true }"
        :selectedFields="[{ field: 'message', type: 'text' }]"
        :searchNode="previewSearchNode"
      ></event-list>
    </div>
  </span>
  <b-tag v-else rounded type="is-light" style="opacity: 0.5">
    <span class="icon is-medium"><i class="fas fa-eye-slash" aria-hidden="true"></i></span>0
  </b-tag>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import EventList from '../Explore/EventList'

export default {
  components: { EventList },
  props: ['searchQuery'],
  data() {
    return {
      previewData: [],
      responseMeta: null,
      previewSearchNode: null,
      isOpen: false,
      timer: null,
    }
  },
  methods: {
    refreshPreview: function () {
      var formData = { query: this.searchQuery, parent: this.currentSearchNode.id }
      ApiClient.search(this.sketch.id, formData).then((response) => {
        this.previewData = response.data.objects
        this.previewSearchNode = response.data.meta.search_node
      })
    },
    delayDisplay: function (state, timeout) {
      if (!this.previewData.length) {
        return
      }
      clearTimeout(this.timer)
      this.timer = setTimeout(() => {
        this.isOpen = state
      }, timeout)
    },
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    currentSearchNode() {
      return this.$store.state.currentSearchNode || { id: 0 }
    },
  },
  mounted() {
    this.refreshPreview()
  },
  watch: {
    searchQuery: function (newQuery) {
      this.refreshPreview(newQuery)
    },
  },
}
</script>

<style scoped lang="scss">
.preview-box {
  z-index: 100;
  position: absolute;
  background: var(--background-color);
  width: 60%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
  height: 50%;
  overflow: scroll;
}

.preview-title {
  padding: 5px;
}
</style>
