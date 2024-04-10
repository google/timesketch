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
  <div>
    <v-row>
      <v-col :cols="event.showComments ? 8 : 0">
        <v-card outlined height="100%">
          <v-simple-table dense>
            <template v-slot:default>
              <tbody>
                <tr
                  v-for="(value, key) in fullEventFiltered"
                  :key="key"
                  @mouseover="c_key = key"
                  @mouseleave="c_key = -1"
                >
                  <!-- Event field name actions -->
                  <td v-if="key == c_key" class="text-right" style="min-width: 105px">
                    <!-- Open aggregation dialog for this field -->
                    <v-btn
                      v-if="!ignoredAggregatorFields.has(key)"
                      @click.stop="loadAggregation(key, value)"
                      icon
                      x-small
                      class="mr-1"
                    >
                      <v-icon title="Aggregation dialog">mdi-chart-bar</v-icon>
                    </v-btn>

                    <!-- Include field:value as filter chip -->
                    <v-btn
                      v-if="!ignoreFilterChips.has(key)"
                      @click.stop="applyFilterChip(key, value, 'must')"
                      icon
                      x-small
                      class="mr-1">
                      <v-icon title="Filter for value">mdi-filter-plus-outline</v-icon>
                    </v-btn>

                    <!-- Exclude field:value as filter chip -->
                    <v-btn
                      v-if="!ignoreFilterChips.has(key)"
                      @click.stop="applyFilterChip(key, value, 'must_not')"
                      icon
                      x-small
                      class="mr-1"
                    >
                      <v-icon title="Filter out value">mdi-filter-minus-outline</v-icon>
                    </v-btn>

                    <!-- Copy field name -->
                    <v-btn
                      icon
                      x-small
                      style="cursor: pointer"
                      @click="copyToClipboard(key)"
                      class="pr-1"
                    >
                      <v-icon title="Copy attribute name" small>mdi-content-copy</v-icon>
                    </v-btn>
                  </td>

                  <td v-else>
                    <div class="px-12"></div>
                  </td>

                  <!-- Event field name -->
                  <td>
                    {{ key }}
                  </td>

                  <!-- Event field value action icons -->
                  <td v-if="checkContextLinkDisplay(key, value) || key == c_key" class="text-right pr-1">
                    <!-- Copy event value -->
                    <v-btn icon x-small style="cursor: pointer" @click="copyToClipboard(value)" v-show="key == c_key">
                      <v-icon small title="Copy attribute value">mdi-content-copy</v-icon>
                    </v-btn>
                    <!-- Context link submenu -->
                    <v-menu v-if="checkContextLinkDisplay(key, value)" offset-y transition="slide-y-transition">
                      <template v-slot:activator="{ on, attrs }">
                        <v-btn icon color="primary" x-small style="cursor: pointer" v-bind="attrs" v-on="on">
                          <v-icon title="Context Lookup" small> mdi-open-in-new </v-icon>
                        </v-btn>
                      </template>
                      <v-list dense>
                        <!-- redirect dialog -->
                        <v-dialog v-model="redirectWarnDialog" max-width="515" :retain-focus="false">
                          <ts-link-redirect-warning
                            app
                            @cancel="redirectWarnDialog = false"
                            :context-value="contextValue"
                            :context-url="contextUrl"
                          ></ts-link-redirect-warning>
                        </v-dialog>
                        <!-- unfurl dialog -->
                        <v-dialog
                          v-model="dfirUnfurlDialog"
                          max-width="80%"
                          min-width="1000px"
                          max-height="80%"
                          min-height="600px"
                          :retain-focus="false"
                          class="asdf"
                        >
                          <ts-unfurl-dialog @cancel="dfirUnfurlDialog = false" :url="contextValue"></ts-unfurl-dialog>
                        </v-dialog>
                        <!-- XML prettify dialog -->
                        <v-dialog v-model="formatXMLString">
                          <ts-format-xml-string
                            @close="formatXMLString = false"
                            :xmlString="value"
                          ></ts-format-xml-string>
                        </v-dialog>

                        <v-list-item
                          v-for="(item, index) in getContextLinkItems(key)"
                          :key="index"
                          style="cursor: pointer"
                          @click.stop="contextLinkRedirect(key, item, value)"
                        >
                          <v-list-item-title v-if="getContextLinkRedirectState(key, item)">
                            {{ item }} (ext.)</v-list-item-title
                          >
                          <v-list-item-title v-else>{{ item }}</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-menu>
                  </td>
                  <td v-else>
                    <div class="px-5"></div>
                  </td>

                  <!-- Event field value -->
                  <td width="100%" class="pl-0">
                    {{ value }}
                  </td>
                </tr>
              </tbody>
            </template>
          </v-simple-table>
        </v-card>
      </v-col>
      <v-slide-x-reverse-transition>
        <v-col cols="4" v-show="event.showComments">
          <ts-comments :comments="comments" :event="event" :currentSearchNode="currentSearchNode"></ts-comments>
        </v-col>
      </v-slide-x-reverse-transition>
    </v-row>
    <v-dialog scrollable v-model="aggregatorDialog" @click:outside="($event) => (this.aggregatorDialog = false)">
      <ts-aggregate-dialog
        :eventKey="eventKey"
        :eventValue="eventValue"
        :eventTimestamp="eventTimestamp"
        :eventTimestampDesc="eventTimestampDesc"
        :reloadData="aggregatorDialog"
        @cancel="aggregatorDialog = false"
      >
      </ts-aggregate-dialog>
    </v-dialog>
    <br />
  </div>
</template>

<script>
import EventBus from '../../event-bus.js'
import ApiClient from '../../utils/RestApiClient'
import TsAggregateDialog from './AggregateDialog.vue'
import TsFormatXmlString from './FormatXMLString.vue'
import TsLinkRedirectWarning from './LinkRedirectWarning.vue'
import TsComments from './Comments.vue'
import TsUnfurlDialog from './UnfurlDialog.vue'

export default {
  components: {
    TsAggregateDialog,
    TsFormatXmlString,
    TsLinkRedirectWarning,
    TsComments,
    TsUnfurlDialog,
  },
  props: ['event'],
  data() {
    return {
      fullEvent: {},
      comments: [],
      aggregatorDialog: false,
      ignoredAggregatorFields: new Set([
        'datetime',
        'message',
        'path_spec',
        'strings',
        'timestamp',
        'xml_string',
      ]),
      ignoreFilterChips: new Set([
        'datetime',
        'tag',
      ]),
      eventKey: '',
      eventValue: '',
      eventTimestamp: 0,
      eventTimestampDesc: '',
      formatXMLString: false,
      redirectWarnDialog: false,
      dfirUnfurlDialog: false,
      contextUrl: '',
      contextValue: '',
      c_key: -1,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    currentUser() {
      return this.$store.state.currentUser
    },
    currentSearchNode() {
      return this.$store.state.currentSearchNode
    },
    fullEventFiltered() {
      Object.getOwnPropertyNames(this.fullEvent).forEach((key) => {
        // Remove internal properties from the UI
        if (key.startsWith('__ts')) {
          delete this.fullEvent[key]
        }
      })
      return this.fullEvent
    },
    contextLinkConf() {
      return this.$store.state.contextLinkConf
    },
  },
  methods: {
    getEvent: function () {
      let searchindexId = this.event._index
      let eventId = this.event._id
      ApiClient.getEvent(this.sketch.id, searchindexId, eventId)
        .then((response) => {
          this.fullEvent = response.data.objects
          this.comments = response.data.meta.comments
          this.eventTimestamp = new Date(response.data.objects.datetime).getTime()
          this.eventTimestampDesc = response.data.objects.timestamp_desc
          if (this.comments.length > 0) {
            this.event.showComments = true
          }
        })
        .catch((e) => {})
    },
    getContextLinkItems(key) {
      let fieldConfList = this.contextLinkConf[key.toLowerCase()] ? this.contextLinkConf[key.toLowerCase()] : []
      let shortNameList = fieldConfList.map((x) => x.short_name)
      return shortNameList
    },
    checkContextLinkDisplay(key, value) {
      const fieldConfList = this.contextLinkConf[key.toLowerCase()] ? this.contextLinkConf[key.toLowerCase()] : []
      for (const confItem of fieldConfList) {
        if (confItem['validation_regex'] !== '' && confItem['validation_regex'] !== undefined) {
          let validationPattern = confItem['validation_regex']
          let regexIdentifiers = validationPattern.slice(validationPattern.lastIndexOf('/') + 1)
          let regexPattern = validationPattern.slice(
            validationPattern.indexOf('/') + 1,
            validationPattern.lastIndexOf('/')
          )
          let valueRegex = new RegExp(regexPattern, regexIdentifiers)
          if (valueRegex.test(value)) {
            return true
          } else {
            return false
          }
        } else {
          return true
        }
      }
      return false
    },
    contextLinkRedirect(key, item, value) {
      const fieldConfList = this.contextLinkConf[key.toLowerCase()] ? this.contextLinkConf[key.toLowerCase()] : []
      for (const confItem of fieldConfList) {
        if (confItem['short_name'] === item) {
          if (confItem['type'] === 'hardcoded_modules') {
            if (confItem['module'] === 'xml_formatter') {
              this.formatXMLString = true
              this.contextValue = value
              return
            }
            if (confItem['module'] === 'unfurl_graph') {
              this.dfirUnfurlDialog = true
              this.contextValue = value
              return
            }
            if (confItem['module'] === 'threat_intel') {
              EventBus.$emit('addIndicator', value)
              return
            }
          } else {
            if (confItem['redirect_warning']) {
              this.redirectWarnDialog = true
              this.contextValue = value
              this.contextUrl = confItem['context_link'].replace('<ATTR_VALUE>', encodeURIComponent(value))
            } else {
              window.open(confItem['context_link'].replace('<ATTR_VALUE>', encodeURIComponent(value)), '_blank')
              this.redirectWarnDialog = false
            }
          }
        }
      }
    },
    getContextLinkType(key, item) {
      const fieldConfList = this.contextLinkConf[key.toLowerCase()] ? this.contextLinkConf[key.toLowerCase()] : []
      for (const confItem of fieldConfList) {
        if (confItem['short_name'] === item) {
          return confItem['type']
        }
      }
    },
    getContextLinkRedirectState(key, item) {
      const fieldConfList = this.contextLinkConf[key.toLowerCase()] ? this.contextLinkConf[key.toLowerCase()] : []
      for (const confItem of fieldConfList) {
        if (confItem['short_name'] === item) {
          if (confItem['redirect_warning']) {
            return confItem['redirect_warning']
          } else {
            return false
          }
        }
      }
    },
    loadAggregation(eventKey, eventValue) {
      this.eventKey = eventKey
      this.eventValue = eventValue
      this.aggregatorDialog = true
    },
    copyToClipboard(content) {
      try {
        navigator.clipboard.writeText(content)
        this.infoSnackBar('copied')
      } catch (error) {
        this.errorSnackBar('Failed copying to the clipboard!')
        console.error(error)
      }
    },
    applyFilterChip(key, value, operator) {
      let eventData = {}
      eventData.doSearch = true
      let chip = {
        field: key,
        value: value,
        type: 'term',
        operator: operator,
        active: true,
      }
      eventData.chip = chip
      EventBus.$emit('setQueryAndFilter', eventData)
    },
  },
  created: function () {
    this.getEvent()
  },
}
</script>

<style lang="scss">
.flexcard {
  display: flex;
  flex-direction: column;
}
</style>
