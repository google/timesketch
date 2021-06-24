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
  <div style="display:inline;">
    <span
      class="ioc-match"
      ref="contextMenuParent"
      @click="event => $refs.contextMenu.open(event, $attrs.text, $refs.contextMenuParent)"
    >
      <slot></slot>
    </span>
    <TsContextMenu ref="contextMenu">
      <template v-slot="params">
        <div v-if="params.data" class="box ioc-context-menu">
          <table>
            <tr>
              <th>IOC</th>
              <th>Type</th>
              <th colspan="3" style="text-align:center;">Actions</th>
            </tr>
            <tr>
              <td>{{ matchIOC.ioc }}</td>
              <td v-if="matchIOC.type">{{ matchIOC.type }}</td>
              <td v-else>
                <b-field>
                  <b-select placeholder="IOC type" v-model="manualIOCType">
                    <option v-for="option in IOCTypes" :value="option.type" :key="option.type">
                      {{ option.type }}
                    </option>
                  </b-select>
                </b-field>
              </td>

              <td class="actions">
                <span
                  class="icon is-small"
                  title="Apply 'Include' filter"
                  v-on:click="addFilter(attributeKey, matchIOC.ioc, 'must')"
                  ><i class="fas fa-search-plus"></i
                ></span>
                <span class="icon is-small" title="Send to threat intelligence" v-on:click="saveThreatIntel(matchIOC)"
                  ><i class="fas fa-brain"></i
                ></span>
              </td>
            </tr>
          </table>
        </div>
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
      manualIOCType: null,
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
    saveThreatIntel: function(ioc) {
      ApiClient.getSketchAttributes(this.sketch.id).then(response => {
        let attributes = response.data
        if (!attributes.intelligence_local) {
          attributes.intelligence_local = { ontology: 'intelligence', value: { data: [] } }
        }

        if (attributes.intelligence_local.value.data.map(ioc => ioc.ioc).indexOf(ioc.ioc) >= 0) {
          return
        }
        if (!ioc.type) {
          ioc.type = this.manualIOCType
        }
        attributes.intelligence_local.value.data.push(ioc)
        ApiClient.addSketchAttribute(
          this.sketch.id,
          'intelligence_local',
          attributes.intelligence_local.value,
          'intelligence'
        ).then(() => {
          this.manualIOCType = null
          Snackbar.open({
            message: 'Attribtue added succesfully',
            type: 'is-white',
            position: 'is-top',
            actionText: 'View intelligence',
            indefinite: false,
            onAction: () => {
              this.$router.push({ name: 'Intelligence' })
            },
          })
          console.log('Attribute added successfully')
        })
      })
    },
  },
  computed: {
    matchIOC() {
      for (let iocType of this.IOCTypes) {
        let matches = iocType.regex.exec(this.$attrs.text)
        if (matches) {
          return { ioc: this.$attrs.text, type: iocType.type }
        }
      }
      return { ioc: this.$attrs.text, type: null }
    },
    sketch() {
      return this.$store.state.sketch
    },
  },
}
</script>

<style scoped lang="scss">
.ioc-match {
  background-color: #ddd;
}

.ioc-match:hover {
  cursor: pointer;
}

.text__highlight {
  background: none;
  border-radius: 0%;
}

.actions .icon {
  cursor: pointer;
  margin-right: 1em;
}
</style>
