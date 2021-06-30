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
  <div style="display:inline;">
    <span
      class="ioc-match"
      ref="contextMenuParent"
      @click="event => this.$refs.contextMenu.open(event, getIOC($attrs.text), $refs.contextMenuParent)"
    >
      <slot></slot>
    </span>
    <TsContextMenu ref="contextMenu">
      <template v-slot="params">
        <section v-if="params.data" class="box ioc-context-menu">
          <div class="ioc-display">
            <span
              class="icon is-small"
              title="Apply 'Include' filter"
              @click="addFilter(attributeKey, params.data.ioc, 'must')"
              ><i class="fas fa-search-plus"></i
            ></span>
            <pre>{{ params.data.ioc }}</pre>
          </div>
          <b-field v-if="!isInIntelligence(params.data)" grouped message="Add to local intelligence">
            <b-select size="is-small" placeholder="IOC type" v-model="params.data.type">
              <option v-for="option in IOCTypes" :value="option.type" :key="option.type">
                {{ option.type }}
              </option>
            </b-select>
            <b-button size="is-small" type="is-primary" @click="saveThreatIntel(params.data)">Add</b-button>
          </b-field>
          <div v-else>
            <small>Already added to <router-link :to="{ name: 'Intelligence' }">Intelligence</router-link></small>
          </div>
        </section>
      </template>
    </TsContextMenu>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsContextMenu from './TsContextMenu'
import { SnackbarProgrammatic as Snackbar } from 'buefy'

export default {
  components: {
    TsContextMenu,
  },
  props: ['attributeKey'],
  name: 'TsIOCMenu',
  data() {
    return {
      IOCTypes: [
        { regex: /[0-9]{1,3}(\.[0-9]{1,3}\.)/g, type: 'ip' },
        { regex: /[0-9a-f]{64}/gi, type: 'hash_sha256' },
        { regex: /[0-9a-f]{40}/gi, type: 'hash_sha1' },
        { regex: /[0-9a-f]{32}/gi, type: 'hash_md5' },
      ],
      iocColumns: [
        { field: 'ioc', label: 'IOC' },
        { field: 'type', label: 'Type' },
      ],
      selectedIOC: {},
    }
  },
  methods: {
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
    getIOC: function(text) {
      for (let iocType of this.IOCTypes) {
        let matches = iocType.regex.exec(this.$attrs.text)
        if (matches) {
          return { ioc: this.$attrs.text, type: iocType.type }
        }
      }
      return { ioc: this.$attrs.text, type: null }
    },
    isInIntelligence(ioc) {
      const attributes = this.$store.state.meta.attributes
      if (!attributes.intelligence_local) {
        return false
      }
      if (attributes.intelligence_local.value.data.map(ioc => ioc.ioc).indexOf(ioc.ioc) >= 0) {
        return true
      }
      return false
    },
    saveThreatIntel: function(ioc) {
      ApiClient.getSketchAttributes(this.sketch.id).then(response => {
        let attributes = response.data
        if (!attributes.intelligence_local) {
          attributes.intelligence_local = { ontology: 'intelligence', value: { data: [] } }
        }

        if (attributes.intelligence_local.value.data.map(ioc => ioc.ioc).indexOf(ioc.ioc) >= 0) {
          return
        }
        attributes.intelligence_local.value.data.push(ioc)
        ApiClient.addSketchAttribute(
          this.sketch.id,
          'intelligence_local',
          attributes.intelligence_local.value,
          'intelligence'
        ).then(() => {
          Snackbar.open({
            message: 'Attribtue added successfully',
            type: 'is-white',
            position: 'is-top',
            actionText: 'View intelligence',
            indefinite: false,
            onAction: () => {
              this.$router.push({ name: 'Intelligence' })
            },
          })
          // refresh computed property based on attributes
          this.$store.state.meta.attributes = attributes
        })
      })
    },
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  mounted() {},
}
</script>

<style lang="scss">
.ioc-match {
  background-color: var(--highlight-color);
}

.ioc-display .icon {
  cursor: pointer;
  margin-right: 0.5em;
}
.ioc-context-menu div.ioc-display {
  margin-bottom: 1em;
  margin-top: 0.4em;
}

.box.ioc-context-menu pre {
  display: inline;
  padding: 0.7em;
}

.box.ioc-context-menu {
  padding: 0.7em;
}

.ioc-match:hover {
  cursor: pointer;
}

.text__highlight {
  background: none;
  border-radius: 0%;
}
</style>
