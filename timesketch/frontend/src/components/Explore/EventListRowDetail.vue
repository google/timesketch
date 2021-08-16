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
  <table class="table is-bordered" style="width:100%;table-layout: fixed;" @mouseup="handleSelectionChange">
    <tbody>
      <tr v-for="(item, key) in fullEventFiltered" :key="key" @mouseover="c_key = key" @mouseleave="c_key = -1">
        <td style="width:40px;">
          <span
            class="icon is-small"
            style="cursor:pointer;"
            title="Apply 'Include' filter"
            v-on:click="addFilter(key, item, 'must')"
            ><i class="fas fa-search-plus"></i
          ></span>
        </td>
        <td style="width:40px;">
          <span
            class="icon is-small"
            style="cursor:pointer;"
            title="Apply 'Exclude' filter"
            v-on:click="addFilter(key, item, 'must_not')"
            ><i class="fas fa-search-minus"></i
          ></span>
        </td>

        <td style="word-wrap: break-word; width: 150px;">
          {{ key }}
          <span
            v-if="key == c_key"
            class="icon is-small"
            style="cursor:pointer;"
            title="Copy key"
            v-clipboard:copy="key"
            v-clipboard:success="handleCopyStatus"
            ><i class="fas fa-copy"></i
          ></span>
        </td>
        <td>
          <span
            v-if="key == c_key"
            class="icon is-small"
            style="cursor:pointer; margin-left: 3px; float:right;"
            title="Copy value"
            v-clipboard:copy="item"
            v-clipboard:success="handleCopyStatus"
            ><i class="fas fa-copy"></i
          ></span>
          <text-highlight
            @addChip="$emit('addChip', $event)"
            :highlightComponent="TsIOCMenu"
            :queries="Object.values(regexes)"
            :attributeKey="key"
            >{{ item }}</text-highlight
          >
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsIOCMenu from '../Common/TsIOCMenu'
import TextHighlight from 'vue-text-highlight'

export default {
  components: { TextHighlight },
  props: ['event'],
  data() {
    return {
      TsIOCMenu,
      regexes: {
        ip: /[0-9]{1,3}(\.[0-9]{1,3}\.)/g,
        hash_md5: /[0-9a-f]{32}/gi,
        hash_sha1: /[0-9a-f]{40}/gi,
        hash_sha256: /[0-9a-f]{64}/gi,
        selection: '',
      },
      c_key: -1,
      fullEvent: {},
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    fullEventFiltered() {
      Object.getOwnPropertyNames(this.fullEvent).forEach(key => {
        // Remove internal properties from the UI
        if (key.startsWith('__ts')) {
          delete this.fullEvent[key]
        }
      })
      return this.fullEvent
    },
  },
  methods: {
    getEvent: function() {
      let searchindexId = this.event._index
      let eventId = this.event._id
      ApiClient.getEvent(this.sketch.id, searchindexId, eventId)
        .then(response => {
          this.fullEvent = response.data.objects
        })
        .catch(e => {})
    },
    addFilter: function(field, value, operator) {
      let chip = {
        field: field,
        value: value,
        type: 'term',
        operator: operator,
        active: true,
      }
      this.$emit('addChip', chip)
    },
    handleCopyStatus: function() {
      this.$buefy.notification.open('Copied!')
    },
    handleSelectionChange(event) {
      if (event.target.closest('.ioc-match') || event.target.closest('.ioc-context-menu')) {
        return
      }
      const text = window.getSelection().toString()
      this.regexes.selection = text
      if (this.regexes.selection !== '') {
      }
    },
  },
  created: function() {
    this.getEvent()
  },
}
</script>
