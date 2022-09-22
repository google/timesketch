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
  <v-simple-table dense>
    <template v-slot:default>
      <thead>
        <tr>
          <th class="text-left">Name</th>
          <th class="text-left">Import method</th>
          <th class="text-left">Events</th>
          <th class="text-left">Uploaded by</th>
          <th class="text-left">Created</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="timeline in activeTimelines" :key="timeline.id">
          <td>
            <v-menu offset-y content-class="menu-with-gap">
              <template v-slot:activator="{ on }">
                <span v-on="on" style="cursor: pointer">
                  <v-avatar rounded :color="'#' + timeline.color" size="24" class="mr-2"> </v-avatar>
                  {{ timeline.name }}
                </span>
              </template>
              <v-card width="300">
                <v-list>
                  <v-list-item>
                    <v-list-item-action>
                      <v-icon>mdi-square-edit-outline</v-icon>
                    </v-list-item-action>
                    <v-list-item-subtitle>Rename timeline</v-list-item-subtitle>
                  </v-list-item>

                  <v-list-item>
                    <v-list-item-action>
                      <v-icon>mdi-magnify</v-icon>
                    </v-list-item-action>
                    <v-list-item-subtitle>
                      <router-link
                        style="text-decoration: none"
                        :to="{ name: 'Explore', query: { timeline: timeline.id } }"
                      >
                        Explore this timeline
                      </router-link>
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item @click="removeChip(chip)">
                    <v-list-item-action>
                      <v-icon>mdi-delete</v-icon>
                    </v-list-item-action>
                    <v-list-item-subtitle>Remove from sketch</v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </v-card>
            </v-menu>
          </td>
          <td>
            {{ timeline.datasources[0].provider }}
            <v-dialog v-model="dialog" width="600">
              <template v-slot:activator="{ on, attrs }">
                <small v-bind="attrs" v-on="on">(details)</small>
              </template>

              <v-card>
                <v-app-bar flat dense>Detailed information for: {{ timeline.name }}</v-app-bar>
                <v-card-text class="pa-5">
                  <ul style="list-style-type: none">
                    <li><strong>Opensearch index: </strong>{{ timeline.searchindex.index_name }}</li>
                    <li>
                      <strong>Number of events: </strong>
                      {{ meta.stats_per_timeline[timeline.id]['count'] | compactNumber }} ({{
                        meta.stats_per_timeline[timeline.id]['count']
                      }})
                    </li>
                    <li><strong>Created by: </strong>{{ timeline.user.username }}</li>
                    <li>
                      <strong>Created at: </strong>{{ timeline.created_at | shortDateTime }}
                      <small>({{ timeline.created_at | timeSince }})</small>
                    </li>
                  </ul>

                  <br /><br />
                  <v-alert
                    v-for="datasource in timeline.datasources"
                    :key="datasource.id"
                    colored-border
                    :color="datasource.error_message ? 'error' : 'success'"
                    border="left"
                    elevation="1"
                  >
                    <ul style="list-style-type: none">
                      <li><strong>Provider:</strong> {{ datasource.provider }}</li>
                      <li><strong>Context:</strong> {{ datasource.context }}</li>
                      <li><strong>User:</strong> {{ datasource.user.username }}</li>
                      <li><strong>File on disk:</strong> {{ datasource.file_on_disk }}</li>
                      <li><strong>File size:</strong> {{ datasource.file_size | compactBytes }}</li>
                      <li><strong>Original filename:</strong> {{ datasource.original_filename }}</li>
                      <li><strong>Data label:</strong> {{ datasource.data_label }}</li>
                    </ul>
                  </v-alert>
                </v-card-text>

                <v-divider></v-divider>

                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn color="primary" text @click="dialog = false"> Close </v-btn>
                </v-card-actions>
              </v-card>
            </v-dialog>
          </td>
          <td>{{ meta.stats_per_timeline[timeline.id]['count'] | compactNumber }}</td>
          <td>{{ timeline.user.username }}</td>
          <td>
            {{ timeline.created_at | shortDateTime }} <small>({{ timeline.created_at | timeSince }})</small>
          </td>
        </tr>
      </tbody>
    </template>
  </v-simple-table>
</template>

<script>
export default {
  props: [],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },

    activeTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.active_timelines]
      return timelines.sort(function (a, b) {
        return a.name.localeCompare(b.name)
      })
    },
  },
  data() {
    return {
      dialog: false,
    }
  },
  methods: {},
}
</script>
