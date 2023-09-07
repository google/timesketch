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
  <div
    :class="
      $vuetify.theme.dark
        ? expanded
          ? 'dark-hover dark-bg'
          : 'dark-hover'
        : expanded
        ? 'light-hover light-bg'
        : 'light-hover'
    "
  >
    <v-divider></v-divider>
    <div
      v-if="timeline.analysis_status === 'PENDING' || timeline.analysis_status === 'STARTED'"
      class="pa-2 pl-3"
      style="display: flex; align-items: center"
      :class="
        $vuetify.theme.dark
          ? expanded
            ? 'dark-hover dark-bg'
            : 'dark-hover'
          : expanded
          ? 'light-hover light-bg'
          : 'light-hover'
      "
    >
      <v-icon class="mr-2" :color="'#' + timeline.color">mdi-circle</v-icon>
      <span class="mr-2" style="color: grey">{{ timeline.name }}</span>
      <v-progress-circular :size="20" :width="1" indeterminate color="primary"></v-progress-circular>
    </div>
    <div
      v-else
      class="pa-2 pl-3"
      style="cursor: pointer; display: flex; align-items: center"
      @click="expanded = !expanded"
      :class="
        $vuetify.theme.dark
          ? expanded
            ? 'dark-hover dark-bg'
            : 'dark-hover'
          : expanded
          ? 'light-hover light-bg'
          : 'light-hover'
      "
    >
      <v-icon class="mr-2" :color="'#' + timeline.color">mdi-circle</v-icon>
      <span>{{ timeline.name }}</span>
      <div v-if="timeline.analysis_status === 'ERROR'">
        <v-tooltip top>
          <template v-slot:activator="{ on }">
            <v-btn text x-small icon v-on="on" class="ml-1" :ripple="false">
              <v-icon small class="ml-1">mdi-alert</v-icon>
            </v-btn>
          </template>
          <span>Analyzer Error</span>
        </v-tooltip>
      </div>
      <div v-else-if="checkAnalyzerOutput && !isMultiAnalyzer">
        <v-tooltip top>
          <template v-slot:activator="{ on }">
            <v-btn v-show="!isMultiAnalyzer" text x-small icon v-on="on" class="ml-1" :ripple="false">
              <v-icon small :color="getPriorityColor">mdi-information-outline</v-icon>
            </v-btn>
          </template>
          <span>Result Priority: {{ resultPriority }}</span>
        </v-tooltip>
      </div>
      <div v-else>
        <v-tooltip v-if="!isMultiAnalyzer" top>
          <template v-slot:activator="{ on }">
            <v-btn v-show="!isMultiAnalyzer" text x-small icon v-on="on" class="ml-1" :ripple="false">
              <v-icon small :color="getPriorityColor">mdi-information-outline</v-icon>
            </v-btn>
          </template>
          <span>Result Priority: Note</span>
        </v-tooltip>
      </div>
    </div>

    <v-expand-transition>
      <div
        v-if="!isMultiAnalyzer"
        v-show="expanded"
        :class="
          $vuetify.theme.dark
            ? expanded
              ? 'dark-hover dark-bg'
              : 'dark-hover'
            : expanded
            ? 'light-hover light-bg'
            : 'light-hover'
        "
      >
        <v-simple-table v-if="checkAnalyzerOutput" dense class="ml-2">
          <tbody
            :class="
              $vuetify.theme.dark
                ? expanded
                  ? 'dark-hover dark-bg'
                  : 'dark-hover'
                : expanded
                ? 'light-hover light-bg'
                : 'light-hover'
            "
          >
            <tr class="pr-3">
              <td width="105" style="border: none">
                <strong>Summary:</strong>
              </td>
              <td style="border: none">
                <span>
                  {{ resultSummary || 'loading...' }}
                </span>
              </td>
            </tr>
            <tr>
              <td style="border: none">
                <strong>Priority:</strong>
              </td>
              <td style="border: none">
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
              <td style="border: none">
                <strong>Last run:</strong>
              </td>
              <td style="border: none">
                <span> {{ timeline.created_at }} UTC </span>
              </td>
            </tr>
            <tr>
              <td width="80" style="border: none">
                <strong>Status:</strong>
              </td>
              <td style="border: none">
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
              <td style="border: none">
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
                  @click="searchForTag(tag)"
                >
                  {{ tag }}
                </v-chip>
              </td>
            </tr>
          </tbody>
        </v-simple-table>
        <v-simple-table v-else dense class="ml-2">
          <tbody
            :class="
              $vuetify.theme.dark
                ? expanded
                  ? 'dark-hover dark-bg'
                  : 'dark-hover'
                : expanded
                ? 'light-hover light-bg'
                : 'light-hover'
            "
          >
            <tr class="pr-3">
              <td width="80" style="border: none">
                <strong v-if="timeline.analysis_status === 'ERROR'">Error:</strong>
                <strong v-else>Summary:</strong>
              </td>
              <td style="border: none">
                <span>
                  {{ timeline.verdict }}
                </span>
              </td>
            </tr>
            <tr>
              <td style="border: none">
                <strong>Last run:</strong>
              </td>
              <td style="border: none">
                <span> {{ timeline.created_at }} UTC </span>
              </td>
            </tr>
            <tr>
              <td width="80" style="border: none">
                <strong>Status:</strong>
              </td>
              <td style="border: none">
                <span>
                  {{ timeline.analysis_status }}
                </span>
              </td>
            </tr>
          </tbody>
        </v-simple-table>
      </div>
      <div v-else v-show="expanded" class="ml-3 pb-1 mr-2">
        <v-icon>mdi-alert-octagon-outline</v-icon>
        <span class="ml-1">
          Showing multi analyzer results is not supported in the new UI yet. Please visit the old UI to see these
          results.
        </span>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import EventBus from '../../main'
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
        const parsed = JSON.parse(this.timeline.verdict)
        // normalize null to undefined
        return parsed == null ? undefined : parsed;
      }
      return undefined
    },
    resultSummary: function() {
      return this.verboseAnalyzerOutput && this.verboseAnalyzerOutput.result_summary
    },
    resultPriority: function() {
      return this.verboseAnalyzerOutput && this.verboseAnalyzerOutput.result_priority
    },
    references: function() {
      return this.verboseAnalyzerOutput && this.verboseAnalyzerOutput.references
    },
    resultStatus: function() {
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
        JSON.parse(this.timeline.verdict)
        return true
      } catch (e) {
        return false
      }
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
    searchForTag(tag) {
      let eventData = {}
      eventData.doSearch = true
      eventData.queryString = 'tag:' + '"' + tag + '"'
      eventData.queryFilter = {
        from: 0,
        terminate_after: 40,
        size: 40,
        indices: '_all',
        order: 'asc',
        chips: [],
      }
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
</style>
