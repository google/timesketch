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
    v-if="iconOnly"
    key="iconOnly"
    class="pa-4"
    style="cursor: pointer"
    @click="
      $emit('toggleDrawer')
      expanded = true
    "
  >
    <v-icon left>
      mdi-chart-bar
    </v-icon>
    <div style="height: 1px">
    </div>
  </div>
  <div
    v-else
    key="iconOnly"
  >
    <div
      :style="!(savedVisualizations && savedVisualizations.length) ? '' : 'cursor: pointer'"
      class="pa-4"
      @click="expanded = !expanded"
      :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
    >
      <span>
        <v-icon left>
          mdi-chart-bar
        </v-icon>
        Visualizations
      </span>

      <v-btn
        v-if="expanded || !(savedVisualizations && savedVisualizations.length)"
        icon
        text
        class="float-right mt-n1 mr-n1"
        :to="{ name: 'VisualizationNew' }"
        @click.stop=""
      >
        <v-icon title="Create a new visualization">
          mdi-plus
        </v-icon>
      </v-btn>
      <span
        v-if="!expanded"
        class="float-right"
        style="margin-right: 10px"
      >
        <small
          v-if="savedVisualizations && savedVisualizations.length"
        >
          <strong>
            {{ visualizationCount }}
          </strong>
        </small>
      </span>
    </div>
    <v-expand-transition>
      <div v-show="expanded && savedVisualizations.length">
        <div
          v-for="(savedVisualization, key) in savedVisualizations"
          :key="key"

          style="cursor: pointer; font-size: 0.9em; text-decoration: none"

        >
          <v-row
            no-gutters
            class="pa-2 pl-5"
            :class="$vuetify.theme.dark ? 'dark-hover' : 'light-hover'"
          >
            <v-col
              :class="$vuetify.theme.dark ? 'dark-font' : 'light-font'"
              @click="navigateToSavedVisualization(savedVisualization.id)"
            >

              <span class="d-inline-block text-truncate" style="max-width: 250px">
                <v-icon left small>
                  {{ getIcon(savedVisualization.chart_type) }}
                </v-icon>
                <!-- {{ savedVisualization.name }} -->
                <v-tooltip bottom :disabled="savedVisualization.name && savedVisualization.name.length < 34">
                  <template v-slot:activator="{ on, attrs }">
                    <span
                      v-bind="attrs"
                      v-on="on"
                    >{{ savedVisualization.name }}</span>
                  </template>
                  <span>{{ savedVisualization.name }}</span>
                </v-tooltip>
              </span>

            </v-col>
            <v-col cols="auto">
              <v-menu offset-y>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn
                    small
                    icon
                    v-bind="attrs"
                    v-on="on"
                    class="mr-1"
                  >
                    <v-icon
                      title="Actions"
                      small
                    >
                      mdi-dots-vertical
                    </v-icon>
                  </v-btn>
                </template>
                <v-list dense class="mx-auto">
                  <v-list-item style="cursor: pointer" @click="copyVisualizationIdToClipboard(savedVisualization.id)">
                    <v-list-item-icon>
                      <v-icon small>mdi-identifier</v-icon>
                    </v-list-item-icon>
                    <v-list-item-title>Copy visualization ID</v-list-item-title>
                  </v-list-item>
                  <v-list-item style="cursor: pointer" @click="copyVisualizationUrlToClipboard(savedVisualization.id)">
                    <v-list-item-icon>
                      <v-icon small>mdi-link-variant</v-icon>
                    </v-list-item-icon>
                    <v-list-item-title>Copy link to this visualization</v-list-item-title>
                  </v-list-item>
                  <v-list-item style="cursor: pointer" @click="deleteVisualization(savedVisualization.id)">
                    <v-list-item-icon>
                      <v-icon small>mdi-trash-can</v-icon>
                    </v-list-item-icon>
                    <v-list-item-title>Delete</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </v-col>
          </v-row>
        </div>
      </div>
    </v-expand-transition>
    <v-divider></v-divider>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  props: {
    iconOnly: {
      type: Boolean,
    },
  },
  data: function () {
    return {
      expanded: false,
    }
  },
  methods: {
    copyVisualizationIdToClipboard(savedVisualizationId) {
      try {
        navigator.clipboard.writeText(savedVisualizationId)
        this.infoSnackBar('Saved Visualization ID copied to clipboard')
      } catch (error) {
        this.errorSnackBar('Failed to load Saved Visualization ID into the clipboard!')
        console.error(error)
      }
    },
    copyVisualizationUrlToClipboard(savedVisualizationId) {
      try {
        let url = window.location.origin + '/sketch/' + this.sketch.id + '/visualization/view/' + savedVisualizationId
        navigator.clipboard.writeText(url)
        this.infoSnackBar('Saved Visualization URL copied to clipboard')
      } catch (error) {
        this.errorSnackBar('Failed to load Saved Visualization URL into the clipboard!')
        console.error(error)
      }
    },
    deleteVisualization(savedVisualizationId) {
      if (confirm('Delete Saved Visualization?')) {
        ApiClient.deleteAggregationById(this.sketch.id, savedVisualizationId)
          .then((response) => {
            this.$store.dispatch('updateSavedVisualizationList', this.sketch.id)
            this.infoSnackBar('Saved Visualization has been deleted')
            let params = {
              name: 'VisualizationView',
              params: {
                aggregationId: savedVisualizationId
              }
            }
            let currentPath  = this.$route.fullPath
            let deletedPath = this.$router.resolve(params).route.fullPath

            if (currentPath === deletedPath) {
              this.$router.push({ name: 'VisualizationNew', })
            }
          })
          .catch((e) => {
            this.errorSnackBar('Failed to delete Saved Visualization!')
            console.error(e)
          })
      }
    },
    getIcon(chartType) {
      return {
        'bar': 'mdi-poll mdi-rotate-90',
        'column': 'mdi-chart-bar',
        'line': 'mdi-chart-line',
        'table': 'mdi-table',
        'heatmap': 'mdi-blur-linear',
        'donut': 'mdi-chart-donut',

      }[chartType]
    },
    navigateToSavedVisualization(savedVisualizationId) {
      let params = {
        name: 'VisualizationView',
        params: { aggregationId: savedVisualizationId }
      }
      let nextPath = this.$router.resolve(params).route.fullPath
      let currentPath  = this.$route.fullPath
      if (nextPath !== currentPath) {
        this.$router.push(params)
      }
    }
  },
  computed: {
    savedVisualizations() {
      if (!this.$store.state.savedVisualizations) {
        return []
      }
      return this.$store.state.savedVisualizations.filter(
          (e) => JSON.parse(e.parameters)['aggregator_class'] === 'apex'
      )
    },
    visualizationCount() {
      if (!this.$store.state.savedVisualizations) {
        return 0
      }
      return this.$store.state.savedVisualizations.filter(
          (e) => JSON.parse(e.parameters)['aggregator_class'] === 'apex'
      ).length
    },
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
  },
  mounted() {
    this.$store.dispatch('updateSavedVisualizationList', this.sketch.id)
  },

}
</script>
