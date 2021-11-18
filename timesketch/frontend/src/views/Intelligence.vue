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
      <b-modal :active.sync="showEditModal">
        <section class="box">
          <h1 class="subtitle">Edit IOC</h1>
          <b-field label="Edit IOC" label-position="on-border">
            <b-input custom-class="ioc-input" type="textarea" v-model="editingIoc.ioc"></b-input>
          </b-field>
          <b-field grouped>
            <b-field>
              <b-select placeholder="IOC type" v-model="editingIoc.type" label="IOC type" label-position="on-border">
                <option v-for="option in IOCTypes" :value="option.type" :key="option.type">
                  {{ option.type }}
                </option>
              </b-select>
            </b-field>
            <b-field>
              <b-taginput
                v-model="editingIoc.tags"
                ellipsis
                icon="label"
                placeholder="Add a tag"
                aria-close-label="Delete this tag"
              >
              </b-taginput>
            </b-field>
            <b-field grouped expanded position="is-right">
              <p class="control">
                <b-button type="is-primary" @click="saveIOC()">Save</b-button>
              </p>
              <p class="control">
                <b-button @click="showEditModal = false">Cancel</b-button>
              </p>
            </b-field>
          </b-field>

          <b-field position="is-right"> </b-field>
        </section>
      </b-modal>

      <b-table v-if="intelligenceData.length > 0" :data="intelligenceData">
        <b-table-column field="type" label="IOC Type" v-slot="props">
          <code>{{ props.row.type }}</code>
        </b-table-column>

        <b-table-column field="ioc" label="Indicator data" v-slot="props">
          <router-link :to="{ name: 'Explore', query: generateElasticQuery(props.row.ioc) }">
            <i class="fas fa-search" aria-hidden="true"></i>
          </router-link>
          <code>{{ props.row.ioc }}</code>
        </b-table-column>

        <b-table-column field="tags" label="Tags" v-slot="props">
          <b-taglist>
            <b-tag v-for="tag in props.row.tags" v-bind:key="tag" type="is-info is-light">{{ tag }} </b-tag>
          </b-taglist>
        </b-table-column>

        <b-table-column field="edit" label="" v-slot="props">
          <span class="icon is-small" style="cursor:pointer;" title="Edit IOC" @click="startIOCEdit(props.row)"
            ><i class="fas fa-edit"></i>
          </span>
        </b-table-column>

        <b-table-column field="delete" label="" v-slot="props">
          <span class="icon is-small" style="cursor:pointer;color:red" title="Delete IOC" @click="deleteIoc(props.row)"
            ><i class="fas fa-trash"></i>
          </span>
        </b-table-column>
      </b-table>
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
import { SnackbarProgrammatic as Snackbar } from 'buefy'

export default {
  data() {
    return {
      editingIoc: {},
      showEditModal: false,
      IOCTypes: [
        { regex: /^(\/[\S]+)+$/i, type: 'fs_path' },
        { regex: /^([-\w]+\.)+[a-z]{2,}$/i, type: 'hostname' },
        { regex: /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/g, type: 'ip' },
        { regex: /^[0-9a-f]{64}$/i, type: 'hash_sha256' },
        { regex: /^[0-9a-f]{40}$/i, type: 'hash_sha1' },
        { regex: /^[0-9a-f]{32}$/i, type: 'hash_md5' },
        // Match any "other" selection
        { regex: /./g, type: 'other' },
      ],
    }
  },
  methods: {
    deleteIoc(ioc) {
      if (confirm('Delete IOC?')) {
        var data = this.intelligenceData.filter(i => i.ioc !== ioc.ioc)
        ApiClient.addSketchAttribute(this.sketch.id, 'intelligence', { data: data }, 'intelligence').then(() => {
          this.loadSketchAttributes()
        })
      }
    },
    loadSketchAttributes() {
      this.$store.dispatch('updateSketch', this.$store.state.sketch.id)
    },
    generateElasticQuery(value) {
      let query = `"${value}"`
      return { q: query }
    },
    startIOCEdit(ioc) {
      console.log('startIOCedit')
      this.showEditModal = true
      this.editingIoc = ioc
    },
    saveIOC() {
      console.log('saveioc')
      ApiClient.addSketchAttribute(this.sketch.id, 'intelligence', this.intelligenceAttribute.value, 'intelligence')
        .then(() => {
          console.log('ioc update success')
          Snackbar.open({
            message: 'IOC successfully updated!',
            type: 'is-success',
            position: 'is-top',
            actionText: 'Dismiss',
            indefinite: false,
          })
          this.showEditModal = false
        })
        .catch(e => {
          Snackbar.open({
            message: 'IOC update failed.',
            type: 'is-danger',
            position: 'is-top',
            indefinite: false,
          })
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
    intelligenceAttribute() {
      if (this.meta.attributes.intelligence === undefined) {
        return { ontology: 'intelligence', value: { data: [] }, name: 'intelligence' }
      }
      return this.meta.attributes.intelligence
    },
    intelligenceData() {
      return this.intelligenceAttribute.value.data
    },
  },
  mounted() {
    this.loadSketchAttributes()
  },
}
</script>

<style lang="scss">
.ioc-input {
  font-family: monospace;
}
</style>
