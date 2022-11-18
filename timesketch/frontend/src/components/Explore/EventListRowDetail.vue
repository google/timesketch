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
  <div>
    <div v-for="(item, key) in fullEventFilteredRich" v-bind:key="key" class="rich-attributes">
      <rich-attribute
        :item="item"
        :name="key"
        @setQueryAndFilter="$emit('setQueryAndFilter', $event)"
        @addChip="$emit('addChip', $event)"
      />
    </div>

    <table class="table is-bordered" style="width: 100%; table-layout: fixed" @mouseup="handleSelectionChange">
      <tbody>
        <tr v-for="(item, key) in fullEventFiltered" :key="key">
          <td class="search-modifier">
            <span
              class="icon is-small"
              style="cursor: pointer"
              title="Apply 'Include' filter"
              v-on:click="addFilter(key, item, 'must')"
              ><i class="fas fa-search-plus"></i
            ></span>
          </td>
          <td class="search-modifier">
            <span
              class="icon is-small"
              style="cursor: pointer"
              title="Apply 'Exclude' filter"
              v-on:click="addFilter(key, item, 'must_not')"
              ><i class="fas fa-search-minus"></i
            ></span>
          </td>

          <td class="attribute-key">
            {{ key }}
            <span
              class="icon is-small copy-action copy-action"
              title="Copy key"
              v-clipboard:copy="key"
              v-clipboard:success="handleCopyStatus"
              ><i class="fas fa-copy"></i
            ></span>
          </td>
          <td class="attribute-value">
            <span
              class="icon is-small copy-action"
              title="Copy value"
              v-clipboard:copy="item"
              v-clipboard:success="handleCopyStatus"
              ><i class="fas fa-copy"></i
            ></span>
            <text-highlight
              v-if="getRegexes(key).length > 0"
              @addChip="$emit('addChip', $event)"
              :highlightComponent="TsIOCMenu"
              :queries="getRegexes(key)"
              :attributeKey="key"
              >{{ item }}</text-highlight
            >
            <span v-else>{{ item }} </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsIOCMenu from '../Common/TsIOCMenu'
import TextHighlight from 'vue-text-highlight'
import RichAttribute from './RichAttribute'

export default {
  components: { TextHighlight, RichAttribute },
  props: ['event'],
  data() {
    return {
      TsIOCMenu,
      regexSelection: '',
      regexes: [
        { type: 'fs_path', regex: /(\/[\S]+)+/i, match_field: 'message' },
        { type: 'hostname', regex: /([-\w]+\.)+[a-z]{2,}/i, match_field: 'hostname' },
        {
          type: 'ipv4',
          regex: /((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/g,
          match_field: 'message',
        },
        { type: 'hash_md5', regex: /[0-9a-f]{32}/i, match_field: 'message' },
        { type: 'hash_sha1', regex: /[0-9a-f]{40}/i, match_field: 'message' },
        { type: 'hash_sha256', regex: /[0-9a-f]{64}/i, match_field: 'message' },
      ],
      fullEvent: {},
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    fullEventFiltered() {
      return Object.keys(this.fullEvent)
        .filter((key) => {
          return !key.startsWith('__')
        })
        .reduce((final, key) => {
          final[key] = this.fullEvent[key]
          return final
        }, {})
    },
    fullEventFilteredRich() {
      return Object.keys(this.fullEvent)
        .filter((key) => {
          return key.startsWith('__') && !key.startsWith('__ts')
        })
        .reduce((final, key) => {
          final[key] = this.fullEvent[key]
          return final
        }, {})
    },
  },
  methods: {
    getEvent: function () {
      let searchindexId = this.event._index
      let eventId = this.event._id
      ApiClient.getEvent(this.sketch.id, searchindexId, eventId)
        .then((response) => {
          this.fullEvent = response.data.objects
        })
        .catch((e) => {})
    },
    addFilter: function (field, value, operator) {
      let chip = {
        field: field,
        value: value,
        type: 'term',
        operator: operator,
        active: true,
      }
      this.$emit('addChip', chip)
    },
    handleCopyStatus: function () {
      this.$buefy.notification.open('Copied!')
    },
    handleSelectionChange(event) {
      if (event.target.closest('.ioc-match') || event.target.closest('.ioc-context-menu')) {
        return
      }
      const text = window.getSelection().toString()
      this.regexSelection = text
    },
    getRegexes(key) {
      if (this.regexSelection !== '') {
        return this.regexSelection
      }
      let regexes = Object.values(
        this.regexes.filter((r) => r.match_field === key || r.match_field === '*').map((r) => r.regex)
      )
      if (this.regexSelection !== '') {
        regexes.push(this.regexSelection)
      }
      return regexes
    },
  },
  created: function () {
    this.getEvent()
  },
}
</script>

<style>
span.copy-action {
  opacity: 0;
  cursor: pointer;
  margin-left: 3px;
  float: right;
}

td:hover > span.copy-action {
  opacity: 0.7;
}

.attribute-key {
  word-wrap: break-word;
  width: 150px;
}

td.search-modifier {
  width: 40px;
}

.rich-attributes {
  margin-bottom: 15px;
  float: left;
  margin-right: 15px;
}
</style>
