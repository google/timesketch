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
  <div :class="getHoverTheme">
    <v-divider></v-divider>
    <div
      v-if="timeline.analysis_status === 'PENDING' || timeline.analysis_status === 'STARTED'"
      class="pa-2 pl-3"
      style="display: flex; align-items: center"
      :class="getHoverTheme"
    >
      <v-icon title="Toggle results for this timeline" class="mr-2" :color="'#' + timeline.color">mdi-circle</v-icon>
      <span class="mr-2 timeline-name-ellipsis" style="color: grey; width:82% !important;">{{ timeline.name }}</span>
      <v-progress-circular :size="20" :width="1" indeterminate color="primary"></v-progress-circular>
    </div>
    <div
      v-else
      class="pa-2 pl-3"
      style="cursor: pointer; display: flex; align-items: center"
      @click="expanded = !expanded"
      :class="getHoverTheme"
    >
      <v-icon title="Toggle results for this timeline" class="mr-2" :color="'#' + timeline.color">mdi-circle</v-icon>
      <span class="timeline-name-ellipsis" style="width:82% !important;">{{ timeline.name }}</span>
      <div v-if="timeline.analysis_status === 'ERROR'">
        <v-btn text x-small icon v-on="on" class="ml-1" :ripple="false" style="cursor: default">
          <v-icon title="The analyzer ran into an error" small class="ml-1">mdi-alert</v-icon>
        </v-btn>
      </div>
      <div v-else-if="checkAnalyzerOutput && !isMultiAnalyzer">
        <v-tooltip top>
          <template v-slot:activator="{ on }">
            <v-btn v-show="!isMultiAnalyzer" text x-small icon v-on="on" class="ml-1" :ripple="false" style="cursor: default">
              <v-icon small :color="getPriorityColor">mdi-information-outline</v-icon>
            </v-btn>
          </template>
          <span>Result Priority: {{ resultPriority }}</span>
        </v-tooltip>
      </div>
      <div v-else>
        <v-tooltip v-if="!isMultiAnalyzer" top>
          <template v-slot:activator="{ on }">
            <v-btn v-show="!isMultiAnalyzer" text x-small icon v-on="on" class="ml-1" :ripple="false" style="cursor: default">
              <v-icon small :color="getPriorityColor">mdi-information-outline</v-icon>
            </v-btn>
          </template>
          <span>Result Priority: Note</span>
        </v-tooltip>
      </div>
    </div>

    <v-expand-transition>
      <div v-if="!isMultiAnalyzer" v-show="expanded" :class="getHoverTheme">
        <v-simple-table v-if="checkAnalyzerOutput" dense class="ml-2 borderless">
          <tbody :class="getHoverTheme">
            <tr class="pr-3">
              <td width="105">
                <strong>Summary:</strong>
              </td>
              <td>
                <span>
                  {{ resultSummary || 'loading...' }}
                </span>
              </td>
            </tr>
            <tr>
              <td>
                <strong>Priority:</strong>
              </td>
              <td>
                <span>
                  {{ resultPriority || 'loading...' }}
                </span>
              </td>
            </tr>
            <tr v-if="references !== undefined">
              <td colspan="2" style="border: none">
                <strong>References:</strong>
                <ul>
                  <li v-for="(item, index) in references" :key="index">
                    <a @click="contextLinkRedirect(item)">{{ item }}</a>
                    <v-dialog v-model="redirectWarnDialog" max-width="515" :retain-focus="false">
                      <ts-link-redirect-warning
                        app
                        @cancel="redirectWarnDialog = false"
                        :context-url="contextUrl"
                      ></ts-link-redirect-warning>
                    </v-dialog>
                  </li>
                </ul>
              </td>
            </tr>
            <tr>
              <td>
                <strong>Last run:</strong>
              </td>
              <td>
                <span> {{ timelineCreated }} UTC </span>
              </td>
            </tr>
            <tr>
              <td width="80" style="border: none">
                <strong>Status:</strong>
              </td>
              <td>
                <span>
                  {{ resultStatus || 'loading...' }}
                </span>
              </td>
            </tr>
            <tr v-if="Object.keys(getAnalyzerOutputMetaData).length !== 0">
              <td colspan="2" style="border: none">
                <strong>Result artifacts</strong>
              </td>
            </tr>
            <tr v-for="(item, key) in getAnalyzerOutputMetaData" :key="key">
              <td>
                <strong>{{ key }}:</strong>
              </td>
              <td style="border: none" v-if="key === 'Searches'">
                <v-chip v-for="(view, index) in item" :key="index" @click="setView(view)" outlined class="mr-1" small>
                  {{ view.name }}
                </v-chip>
              </td>
              <td style="border: none" v-if="key === 'Story'">
                <router-link
                  v-for="story in item"
                  :key="story.id"
                  :to="{ name: 'Story', params: { storyId: story.id } }"
                >
                  <v-chip outlined class="mr-1" small link>{{ story.title }}</v-chip>
                </router-link>
              </td>
              <td style="border: none" v-if="key === 'Graphs'">
                <router-link
                  v-for="(graph, index) in item"
                  :key="index"
                  :to="{ name: 'Graph', params: { graph: graph.id === undefined ? graph.name : graph.id } }"
                >
                  <v-chip
                    outlined
                    class="mr-1"
                    small
                    link
                    @click="graph.id === undefined ? setGraphPlugin(graph.name) : setSavedGraph(graph.id)"
                  >
                    {{ graph.id === undefined ? graph.display_name : graph.name }}
                  </v-chip>
                </router-link>
              </td>
              <!-- TODO(jkppr): Add Aggregations as soon as they are supported in the new UI -->
              <td style="border: none" v-if="key === 'Aggregations'">
                <span>Linking aggregations is not supported in the new UI yet.</span>
              </td>
              <td style="border: none" v-if="key === 'Tags'">
                <v-chip
                  v-for="(tag, index) in item"
                  :key="index"
                  color="lightgrey"
                  class="mr-1 mb-1"
                  small
                  @click="applyFilterChip(tag, 'tag', 'term', timeline.id)"
                >
                  {{ tag }}
                </v-chip>
              </td>
              <td style="border: none" v-if="key === 'Attributes'">
                <v-chip
                  v-for="(attribute, index) in item"
                  :key="index"
                  color="lightgrey"
                  class="mr-1 mb-1"
                  small
                  @click="applySearch(`_exists_:${attribute}`, timeline.id)"
                >
                  {{ attribute }}
                </v-chip>
              </td>
            </tr>
          </tbody>
        </v-simple-table>
        <v-simple-table v-else dense class="ml-2 borderless">
          <tbody :class="getHoverTheme">
            <tr class="pr-3">
              <td width="80" style="border: none">
                <strong v-if="timeline.analysis_status === 'ERROR'">Error:</strong>
                <strong v-else>Summary:</strong>
              </td>
              <td>
                <span>
                  {{ timelineResult.verdict }}
                </span>
              </td>
            </tr>
            <tr>
              <td>
                <strong>Last run:</strong>
              </td>
              <td>
                <span> {{ timelineCreated }} UTC </span>
              </td>
            </tr>
            <tr>
              <td width="80" style="border: none">
                <strong>Status:</strong>
              </td>
              <td>
                <span>
                  {{ timeline.analysis_status }}
                </span>
              </td>
            </tr>
          </tbody>
        </v-simple-table>
      </div>
      <div v-else v-show="expanded" :class="getHoverTheme">
        <!-- TODO: iterate on multianalyzer timeline results -->
        <v-simple-table dense class="ml-2 borderless">
          <tbody :class="getHoverTheme">
            <tr>
              <td>
                <strong>Type:</strong>
              </td>
              <td>
                <span> Multi analyzer</span>
              </td>
            </tr>
            <tr>
              <td>
                <strong>Last run:</strong>
              </td>
              <td>
                <span> {{ timelineCreated }} UTC </span>
              </td>
            </tr>
            <tr>
              <td width="80" style="border: none">
                <strong>Status:</strong>
              </td>
              <td>
                <span>
                  {{ timeline.analysis_status }}
                </span>
              </td>
            </tr>
            <tr v-if="timeline.results.length !== 0">
              <td colspan="2" style="border: none">
                <strong>Results:</strong>
              </td>
            </tr>
          </tbody>
        </v-simple-table>
        <v-data-iterator
          :items="timeline.results"
          :items-per-page="10"
          :hide-default-footer="timeline.results.length < 10 ? true : false"
        >
          <template v-slot:default="props">
            <div v-for="(analyzer, index) in props.items" :key="index">
              <v-divider></v-divider>
              <v-row no-gutters class="pa-1 pl-5">
                <span>{{ analyzer.verdict }}</span>
              </v-row>
            </div>
          </template>
        </v-data-iterator>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import EventBus from '../../event-bus.js'
import TsLinkRedirectWarning from '../Explore/LinkRedirectWarning.vue'

export default {
  props: ['timeline', 'isMultiAnalyzer'],
  components: {
    TsLinkRedirectWarning,
  },
  data: function () {
    return {
      expanded: false,
      redirectWarnDialog: false,
      contextUrl: '',
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    graphs() {
      return this.$store.state.graphPlugins
    },
    savedGraphs() {
      return this.$store.state.savedGraphs
    },
    verboseAnalyzerOutput: function () {
      if (this.checkAnalyzerOutput) {
        // this can return null
        const parsed = JSON.parse(this.timelineResult.verdict)
        // normalize null to undefined
        return parsed == null ? undefined : parsed
      }
      return undefined
    },
    resultSummary: function () {
      return this.verboseAnalyzerOutput && this.verboseAnalyzerOutput.result_summary
    },
    resultPriority: function () {
      return this.verboseAnalyzerOutput && this.verboseAnalyzerOutput.result_priority
    },
    references: function () {
      return this.verboseAnalyzerOutput && this.verboseAnalyzerOutput.references
    },
    resultStatus: function () {
      return this.verboseAnalyzerOutput && this.verboseAnalyzerOutput.result_status
    },
    getAnalyzerOutputMetaData: function () {
      let metaData = {}
      if (this.verboseAnalyzerOutput !== undefined && this.verboseAnalyzerOutput.platform_meta_data !== undefined) {
        if (this.verboseAnalyzerOutput.platform_meta_data.saved_views !== undefined) {
          metaData['Searches'] = []
          for (const id of this.verboseAnalyzerOutput.platform_meta_data.saved_views) {
            let view = this.meta.views.find((view) => view.id === id)
            if (view !== undefined) {
              metaData['Searches'].push(view)
            }
          }
        }
        if (this.verboseAnalyzerOutput.platform_meta_data.saved_stories !== undefined) {
          metaData['Story'] = []
          for (const id of this.verboseAnalyzerOutput.platform_meta_data.saved_stories) {
            let storie = this.meta.stories.find((storie) => storie.id === id)
            if (storie !== undefined) {
              metaData['Story'].push(storie)
            }
          }
        }
        if (this.verboseAnalyzerOutput.platform_meta_data.saved_graphs !== undefined) {
          metaData['Graphs'] = []
          for (const id of this.verboseAnalyzerOutput.platform_meta_data.saved_graphs) {
            if (typeof id === 'number') {
              let savedGraph = this.savedGraphs.find((graph) => graph.id === id)
              if (savedGraph !== undefined) {
                metaData['Graphs'].push(savedGraph)
              }
            } else if (typeof id === 'string') {
              let pluginGraph = this.graphs.find((graph) => graph.name === id)
              if (pluginGraph !== undefined) {
                metaData['Graphs'].push(pluginGraph)
              }
            } else {
              console.error('Saved Graph reference is neither Integer nor String.', typeof id, id)
            }
          }
        }
        if (this.verboseAnalyzerOutput.platform_meta_data.saved_aggregations !== undefined) {
          metaData['Aggregations'] = this.verboseAnalyzerOutput.platform_meta_data.saved_aggregations
        }
        if (this.verboseAnalyzerOutput.platform_meta_data.created_tags !== undefined) {
          metaData['Tags'] = this.verboseAnalyzerOutput.platform_meta_data.created_tags
        }
        if (this.verboseAnalyzerOutput.platform_meta_data.created_attributes !== undefined) {
          metaData['Attributes'] = this.verboseAnalyzerOutput.platform_meta_data.created_attributes
        }
        return metaData
      }
      return metaData
    },
    getPriorityColor: function () {
      if (this.verboseAnalyzerOutput !== undefined && this.verboseAnalyzerOutput.result_priority !== undefined) {
        if (this.verboseAnalyzerOutput.result_priority === 'HIGH') {
          return '#DD2003'
        } else if (this.verboseAnalyzerOutput.result_priority === 'MEDIUM') {
          return '#F89412'
        } else if (this.verboseAnalyzerOutput.result_priority === 'LOW') {
          return '#0E72ED'
        } else if (this.verboseAnalyzerOutput.result_priority === 'NOTE') {
          return '#7F7C7C'
        }
      }
      return '#7F7C7C'
    },
    checkAnalyzerOutput: function () {
      try {
        JSON.parse(this.timelineResult.verdict)
        return true
      } catch (e) {
        return false
      }
    },
    timelineFirstResult: function () {
      return this.timeline && this.timeline.results.length > 0 && this.timeline.results[0]
        ? this.timeline.results[0]
        : undefined
    },
    timelineCreated: function () {
      const firstEntry = this.timelineFirstResult
      if (!firstEntry) return '... invalid date'
      const createdAt =
        (firstEntry.created_at && firstEntry.created_at.split('.').length) > 0
          ? firstEntry.created_at.split('.')[0]
          : '... invalid date'
      return createdAt
    },
    timelineResult: function () {
      return this.timelineFirstResult ? this.timelineFirstResult : '... no results found'
    },
    getHoverTheme: function () {
      return this.$vuetify.theme.dark
        ? this.expanded
          ? 'dark-hover dark-bg'
          : 'dark-hover'
        : this.expanded
        ? 'light-hover light-bg'
        : 'light-hover'
    },
  },
  methods: {
    setView: function (savedSearch) {
      EventBus.$emit('setActiveView', savedSearch)
    },
    setGraphPlugin(graph) {
      EventBus.$emit('setGraphPlugin', graph)
    },
    setSavedGraph(graphId) {
      EventBus.$emit('setSavedGraph', graphId)
    },
    applySearch(searchQuery = '', timelineId = '_all') {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = searchQuery
      eventData.queryFilter = {
        from: 0,
        terminate_after: 40,
        size: 40,
        indices: [timelineId],
        order: 'asc',
        chips: [],
      }
      EventBus.$emit('setQueryAndFilter', eventData)
    },
    applyFilterChip(term, termField = '', termType = 'label', timelineId = '_all') {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = '*'
      eventData.queryFilter = {
        from: 0,
        terminate_after: 40,
        size: 40,
        indices: [timelineId],
        order: 'asc',
        chips: [],
      }
      let chip = {
        field: termField,
        value: term,
        type: termType,
        operator: 'must',
        active: true,
      }
      eventData.chip = chip
      EventBus.$emit('setQueryAndFilter', eventData)
    },
    contextLinkRedirect(item) {
      this.contextUrl = item
      this.redirectWarnDialog = true
    },
  },
}
</script>

<style scoped lang="scss">
.dark-bg {
  background-color: #303030;
}
.light-bg {
  background-color: #f6f6f6;
}
.borderless td {
  border: none !important;
}
</style>
