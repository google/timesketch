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

    <!-- IOC table -->
    <section class="section" v-if="Object.keys(tagMetadata).length > 0">
      <div class="container is-fluid">
        <div class="columns">
          <div class="column">
            <div class="card">
              <div class="card-header">
                <p class="card-header-title">
                  Indicators of compromise
                  <b-button @click="startIOCEdit(getNewIoc(), -1)" type="is-success" size="is-small" class="new-ioc">
                    <i class="fas fa-plus-circle" aria-hidden="true"></i>
                    Add new
                  </b-button>
                </p>
              </div>
              <div class="card-content">
                <b-table v-if="intelligenceData.length > 0" :data="intelligenceData">
                  <b-table-column field="type" label="IOC Type" v-slot="props" sortable>
                    <code>{{ props.row.type }}</code>
                  </b-table-column>

                  <b-table-column field="externalURI" label="External ref." v-slot="props" sortable>
                    <a
                      v-if="getValidUrl(props.row.externalURI)"
                      :href="getValidUrl(props.row.externalURI)"
                      target="_blank"
                    >
                      <i class="fas fa-external-link-alt"></i> {{ getValidUrl(props.row.externalURI).host }}
                    </a>
                    <span v-else>{{ props.row.externalURI }}</span>
                  </b-table-column>

                  <b-table-column field="ioc" label="" v-slot="props" width="10em">
                    <i
                      class="fas fa-copy"
                      style="cursor: pointer"
                      title="Copy IOC to clipboard."
                      v-clipboard:copy="props.row.ioc"
                      v-clipboard:success="notifyClipboardSuccess"
                    ></i>
                    <router-link :to="{ name: 'Explore', query: generateOpenSearchQuery(props.row.ioc) }" class="ml-4">
                      <i
                        class="fas fa-search"
                        aria-hidden="true"
                        title="Search sketch for all events containing this IOC."
                      ></i>
                    </router-link>
                    <explore-preview
                      style="margin-left: 10px"
                      :searchQuery="generateOpenSearchQuery(props.row.ioc)['q']"
                    ></explore-preview>
                  </b-table-column>

                  <b-table-column field="ioc" label="Indicator data" v-slot="props" sortable>
                    <code>{{ props.row.ioc }}</code>
                  </b-table-column>

                  <b-table-column field="tags" label="Tags" v-slot="props">
                    <b-taglist>
                      <b-tag
                        v-for="tag in getEnrichedTags(props.row.tags)"
                        v-bind:key="tag.name"
                        :type="`is-${tag.class} is-light`"
                      >
                        <router-link
                          :to="{ name: 'Explore', query: generateOrOpenSearchQuery(tagInfo[tag.name].iocs) }"
                        >
                          <i
                            class="fas fa-search"
                            aria-hidden="true"
                            title="Search sketch for all IOCs with this tag."
                          ></i>
                        </router-link>
                        {{ tag.name }}
                      </b-tag>
                    </b-taglist>
                  </b-table-column>

                  <b-table-column field="edit" label="" v-slot="props">
                    <span
                      class="icon is-small"
                      style="cursor: pointer"
                      title="Edit IOC"
                      @click="startIOCEdit(props.row, props.index)"
                      ><i class="fas fa-edit"></i>
                    </span>
                  </b-table-column>

                  <b-table-column field="delete" label="" v-slot="props">
                    <span
                      class="icon is-small delete-ioc"
                      style="cursor: pointer"
                      title="Delete IOC"
                      @click="deleteIoc(props.row)"
                      ><i class="fas fa-trash"></i>
                    </span>
                  </b-table-column>
                </b-table>
                <!-- End IOC table, empty palceholder follows -->
                <div v-else class="card-content">
                  Examine events in the <router-link :to="{ name: 'Explore' }">Explore view</router-link> to add
                  intelligence locally
                </div>
              </div>
            </div>
          </div>
          <!-- end column -->
        </div>
        <!-- end columns -->

        <!-- Tag & label list columns -->
        <div class="columns" v-if="Object.keys(tagMetadata).length > 0">
          <!-- tag column -->
          <div class="column">
            <div class="card">
              <div class="card-header">
                <p class="card-header-title">
                  Tag list <i class="fas fa-question-circle" title="Tags that have been associated with IOCs."></i>
                </p>
                <p class="card-header-icon">
                  <span class="icon"> </span>
                </p>
              </div>
              <div class="card-content">
                <b-table
                  v-if="Object.keys(tagInfo).length > 0"
                  :data="Object.values(tagInfo)"
                  default-sort="tag.weight"
                  default-sort-direction="desc"
                >
                  <b-table-column field="search" label="" v-slot="props" width="1em">
                    <router-link :to="{ name: 'Explore', query: generateOrOpenSearchQuery(props.row.iocs) }">
                      <i class="fas fa-search" aria-hidden="true" title="Search sketch for all IOCs with this tag."></i>
                    </router-link>
                  </b-table-column>
                  <b-table-column field="tag.name" label="Tag name" v-slot="props" sortable>
                    <b-tag :type="`is-${props.row.tag.class} is-light`">{{ props.row.tag.name }} </b-tag>
                  </b-table-column>
                  <b-table-column field="count" label="IOCs tagged" v-slot="props" sortable numeric>
                    {{ props.row.count }}
                  </b-table-column>
                  <b-table-column field="tag.weight" label="Weight" v-slot="props" width="2em" sortable>
                    {{ props.row.tag.weight }}
                  </b-table-column>
                </b-table>
                <span v-else>No IOCs have been tagged yet.</span>
              </div>
            </div>
          </div>

          <!-- labels column -->
          <div class="column">
            <div class="card">
              <div class="card-header">
                <p class="card-header-title">
                  Event tags <i class="fas fa-question-circle" title="Tags that have been applied to events."></i>
                </p>
                <p class="card-header-icon">
                  <span class="icon"> </span>
                </p>
              </div>

              <div class="card-content">
                <b-table v-if="sketchTags.length > 0" :data="sketchTags">
                  <b-table-column field="search" label="" v-slot="props" width="1em">
                    <router-link :to="{ name: 'Explore', query: generateOpenSearchQuery(props.row.tag, 'tag') }">
                      <i
                        class="fas fa-search"
                        aria-hidden="true"
                        title="Search sketch for all events with this tag."
                      ></i>
                    </router-link>
                  </b-table-column>
                  <b-table-column field="tag" label="Tag" v-slot="props" sortable>
                    <b-tag type="is-info is-light">{{ props.row.tag }} </b-tag>
                  </b-table-column>
                  <b-table-column field="count" label="Events tagged" v-slot="props" sortable numeric>
                    {{ props.row.count }}
                  </b-table-column>
                </b-table>
                <span v-else>No events have been tagged yet.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container is-fluid"></div>
    </section>
  </div>
</template>

<script>
import _ from 'lodash'
import ApiClient from '../utils/RestApiClient'
import { SnackbarProgrammatic as Snackbar } from 'buefy'
import { IOCTypes } from '../utils/tagMetadata'
import ExplorePreview from '../components/Common/ExplorePreview'
import TsIocCompose from '../components/Common/TsIocCompose'

export default {
  components: { ExplorePreview },
  data() {
    return {
      sketchTags: [],
      tagInfo: {},
      tagMetadata: {},
      editingIoc: {},
      isNew: false,
      showEditModal: false,
      IOCTypes: IOCTypes,
    }
  },
  methods: {
    deleteIoc(ioc) {
      if (confirm('Delete IOC?')) {
        var data = this.intelligenceData.filter((i) => i.ioc !== ioc.ioc)
        ApiClient.addSketchAttribute(this.sketch.id, 'intelligence', { data: data }, 'intelligence').then(() => {
          this.loadSketchAttributes()
        })
      }
    },
    getNewIoc() {
      return {
        ioc: null,
        type: 'other',
        externalURI: null,
        tags: [],
      }
    },
    getValidUrl(urlString) {
      if (urlString === undefined || urlString === null || urlString === '') {
        return false
      }
      if (urlString.startsWith('http')) {
        return new URL(urlString)
      } else if (urlString.includes('/')) {
        return new URL('http://' + urlString)
      } else {
        return false
      }
    },
    loadSketchAttributes() {
      this.$store.dispatch('updateSketch', this.$store.state.sketch.id)
      // buildTagInfo depends on tagMetadata to be present.
      ApiClient.getTagMetadata().then((response) => {
        this.tagMetadata = response.data
        this.buildTagInfo()
      })
    },
    loadSketchTags() {
      ApiClient.runAggregator(this.sketch.id, {
        aggregator_name: 'field_bucket',
        aggregator_parameters: { field: 'tag' },
      }).then((response) => {
        this.sketchTags = response.data.objects[0].field_bucket.buckets
        // of the form [{count: 0, tag: 'foo'}]
      })
    },
    notifyClipboardSuccess() {
      this.$buefy.notification.open({ message: 'Succesfully copied data to clipboard!', type: 'is-success' })
    },
    buildTagInfo() {
      // We need tagMetadata to be embedded in the list below as it is used
      // for sorting in the table.
      this.tagInfo = {}
      for (var ioc of this.intelligenceData) {
        for (var tag of ioc.tags) {
          // deal with the case when tag is an object that is already enriched.
          var tagKey = null
          if (typeof tag === 'object') {
            tagKey = tag.name
          } else {
            tagKey = tag
          }
          if (!this.tagInfo[tagKey]) {
            this.tagInfo[tagKey] = {
              count: 0,
              iocs: [],
              tag: this.enrichTag(tag),
            }
          }
          this.tagInfo[tagKey].count++
          this.tagInfo[tagKey].iocs.push(ioc.ioc)
        }
      }
    },
    getEnrichedTags(tags) {
      let enriched = tags.map((tag) => this.enrichTag(tag)).sort((a, b) => b.weight - a.weight)
      return enriched
    },
    enrichTag(tag) {
      if (typeof tag === 'object') {
        return tag
      } else {
        let tagInfo = { name: tag }
        if (this.tagMetadata[tag]) {
          return _.extend(tagInfo, this.tagMetadata[tag])
        } else {
          for (var regex in this.tagMetadata['regexes']) {
            if (tag.match(regex)) {
              return _.extend(tagInfo, this.tagMetadata['regexes'][regex])
            }
          }
          return _.extend(tagInfo, this.tagMetadata.default)
        }
      }
    },
    // TODO: Use filter chips instead
    generateOrOpenSearchQuery(iocs) {
      let query = iocs.map((v) => `"${v}"`).reduce((a, b) => `${a} OR ${b}`)
      return { q: query }
    },
    generateOpenSearchQuery(value, field) {
      let query = `"${value}"`
      // Escape special OpenSearch characters: \, [space]
      query = query.replace(/[\\\s]/g, '\\$&')
      if (field !== undefined) {
        query = `${field}:${query}`
      }
      return { q: query }
    },
    startIOCEdit(ioc, index) {
      this.$buefy.modal.open({
        parent: this,
        component: TsIocCompose,
        props: { value: ioc },
        events: {
          input: (value) => {
            if (index === -1) {
              this.intelligenceAttribute.value.data.push(value)
            } else {
              // Assigning a value to the array doesn't seem to trigger data refresh, we have to use splice
              this.intelligenceAttribute.value.data.splice(index, 1, value)
            }
            this.saveIntelligence()
          },
        },
      })
    },
    saveIntelligence() {
      // console.log(this.intelligenceAttribute.value)
      ApiClient.addSketchAttribute(this.sketch.id, 'intelligence', this.intelligenceAttribute.value, 'intelligence')
        .then(() => {
          Snackbar.open({
            message: 'Intelligence successfully updated!',
            type: 'is-success',
            position: 'is-top',
            actionText: 'Dismiss',
            indefinite: false,
          })
          this.showEditModal = false
          this.buildTagInfo()
        })
        .catch((e) => {
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
    this.loadSketchTags()
  },
}
</script>

<style lang="scss">
.ioc-input {
  font-family: monospace;
}

.delete-ioc {
  cursor: pointer;
  color: #da1039;
}

.fa-question-circle {
  margin-left: 0.6em;
  opacity: 0.5;
}

.new-ioc i {
  margin-right: 0.5em;
}
.new-ioc {
  margin-left: 0.5em;
}
</style>
