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
      <v-card outlined height="100%">
        Actions:
        <v-btn-group>
          <v-btn icon small @click="copyEventUrlToClipboard(event)">
            <v-tooltip top close-delay="300" :open-on-click="false">
              <template v-slot:activator="{ on }">
                <v-icon v-on="on"> mdi-link </v-icon>
              </template>
              <span>Copy event URL to clipboard</span>
            </v-tooltip>
          </v-btn>
          <v-btn icon small @click="copyEventAsJSON()">
            <v-tooltip top close-delay="300" :open-on-click="false">
              <template v-slot:activator="{ on }">
                <v-icon v-on="on"> mdi-content-copy </v-icon>
              </template>
              <span>Copy event data as JSON to clipboard</span>
            </v-tooltip>
          </v-btn>
          <v-btn small icon @click="toggleStar()">
            <v-icon v-if="event._source.label.includes('__ts_star')" color="amber">mdi-star</v-icon>
            <v-icon v-else>mdi-star-outline</v-icon>
          </v-btn>
          <ts-event-tag-menu :event="event"></ts-event-tag-menu>
          <v-btn icon small @click="searchContext(event)">
            <v-tooltip top close-delay="300" :open-on-click="false">
              <template v-slot:activator="{ on }">
                <v-icon v-on="on"> mdi-magnify </v-icon>
              </template>
              <span>Search +/- 5 min</span>
            </v-tooltip>
          </v-btn>
        </v-btn-group>
      </v-card>
    </v-row>

    <v-row>
      <v-col cols="8">
        <v-card outlined height="100%">
          <v-simple-table dense>
            <template v-slot:default>
              <tbody>
                <tr v-for="(value, key) in fullEventFiltered" :key="key">
                  <td>
                    {{ key }}
                  </td>
                  <td v-if="key.includes('xml') || checkContextLinkDisplay(key, value)" class="px-0">
                    <v-dialog v-if="key.includes('xml')" v-model="formatXMLString" width="1000">
                      <template v-slot:activator="{ on, attrs }">
                        <v-btn
                          icon
                          color="primary"
                          x-small
                          style="cursor: pointer"
                          v-bind="attrs"
                          v-on="on"
                          @click="formatXMLString = true"
                        >
                          <v-tooltip top close-delay="300" :open-on-click="false">
                            <template v-slot:activator="{ on }">
                              <v-icon v-on="on" small> mdi-xml </v-icon>
                            </template>
                            <span>Prettify XML</span>
                          </v-tooltip>
                        </v-btn>
                      </template>
                      <ts-format-xml-string
                        app
                        @cancel="formatXMLString = false"
                        :xmlString="value"
                      ></ts-format-xml-string>
                    </v-dialog>
                    <v-menu v-if="checkContextLinkDisplay(key, value)" offset-y transition="slide-y-transition">
                      <template v-slot:activator="{ on, attrs }">
                        <v-btn icon color="primary" x-small style="cursor: pointer" v-bind="attrs" v-on="on">
                          <v-tooltip top close-delay="300" :open-on-click="false">
                            <template v-slot:activator="{ on }">
                              <v-icon v-on="on" small> mdi-open-in-new </v-icon>
                            </template>
                            <span>Context Lookup</span>
                          </v-tooltip>
                        </v-btn>
                      </template>
                      <v-list dense>
                        <v-list-item
                          v-for="(item, index) in getContextLinkItems(key)"
                          :key="index"
                          style="cursor: pointer"
                          @click.stop="contextLinkRedirect(key, item, value)"
                        >
                          <v-list-item-title v-if="getContextLinkRedirectState(key, item)">{{
                            item
                          }}</v-list-item-title>
                          <v-list-item-title v-else>{{ item }}*</v-list-item-title>
                          <v-dialog v-model="redirectWarnDialog" max-width="515" :retain-focus="false">
                            <ts-link-redirect-warning
                              app
                              @cancel="redirectWarnDialog = false"
                              :context-value="contextValue"
                              :context-url="contextUrl"
                            ></ts-link-redirect-warning>
                          </v-dialog>
                        </v-list-item>
                      </v-list>
                    </v-menu>
                  </td>
                  <td v-else class="px-4"></td>
                  <td width="100%" class="pl-0">
                    {{ value }}
                  </td>
                </tr>
              </tbody>
            </template>
          </v-simple-table>
        </v-card>
      </v-col>
      <v-col cols="4">
        <v-card outlined>
          <v-toolbar dense flat>
            <v-toolbar-title style="font-size: 1.2em">Comments</v-toolbar-title>
          </v-toolbar>

          <v-list three-line>
            <v-list-item
              v-for="(comment, index) in comments"
              :key="comment.id"
              @mouseover="selectComment(comment)"
              @mouseleave="unSelectComment()"
            >
              <v-list-item-avatar>
                <v-avatar color="grey lighten-1">
                  <span class="white--text">{{ comment.user.username.charAt(0).toUpperCase() }}</span>
                </v-avatar>
              </v-list-item-avatar>

              <v-list-item-content>
                <v-list-item-title>
                  {{ comment.user.username }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ comment.created_at | shortDateTime }} ({{ comment.created_at | timeSince }})
                </v-list-item-subtitle>

                <v-card flat v-if="comment.editable" class="mt-5">
                  <v-textarea v-model="comments[index].comment" hide-details auto-grow filled></v-textarea>

                  <v-card-actions v-if="comment.editable">
                    <v-spacer></v-spacer>
                    <v-btn text color="primary" v-if="comment.editable" @click="editComment(index, false)">
                      Cancel
                    </v-btn>
                    <v-btn text color="primary" @click="updateComment(comment, index)"> Save </v-btn>
                  </v-card-actions>
                </v-card>
                <p v-else style="max-width: 90%" class="body-2">{{ comment.comment }}</p>
              </v-list-item-content>

              <v-list-item-action
                v-if="comment === selectedComment && meta.permissions.write && currentUser == comment.user.username"
                style="position: absolute; right: 0"
              >
                <v-chip outlined style="margin-right: 10px">
                  <v-btn icon small @click="editComment(index)">
                    <v-icon small>mdi-square-edit-outline</v-icon>
                  </v-btn>
                  <v-btn icon small @click="deleteComment(comment.id, index)">
                    <v-icon small>mdi-trash-can-outline</v-icon>
                  </v-btn>
                </v-chip>
              </v-list-item-action>
            </v-list-item>
          </v-list>

          <v-card-actions v-if="meta.permissions.write">
            <v-textarea
              v-model="comment"
              hide-details
              auto-grow
              filled
              class="mx-2 mb-2"
              label="Add comment"
              rows="1"
            ></v-textarea>
            <v-btn icon @click="postComment">
              <v-icon>mdi-send</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    <br />
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import EventBus from '../../main'
import TsFormatXmlString from './FormatXMLString.vue'
import TsLinkRedirectWarning from './LinkRedirectWarning.vue'
import TsEventTagMenu from '../../components/Explore/EventTagMenu.vue'

export default {
  components: {
    TsFormatXmlString,
    TsLinkRedirectWarning,
    TsEventTagMenu,
  },
  props: ['event'],
  data() {
    return {
      fullEvent: {},
      comment: '',
      comments: [],
      selectedComment: null,
      formatXMLString: false,
      redirectWarnDialog: false,
      contextUrl: '',
      contextValue: '',
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
        })
        .catch((e) => {})
    },
    postComment: function () {
      EventBus.$emit('eventAnnotated', { type: '__ts_comment', event: this.event, searchNode: this.currentSearchNode })
      ApiClient.saveEventAnnotation(this.sketch.id, 'comment', this.comment, [this.event], this.currentSearchNode)
        .then((response) => {
          this.comments.push(response.data.objects[0][0])
          this.comment = ''
        })
        .catch((e) => {})
    },
    updateComment: function (comment, commentIndex) {
      ApiClient.updateEventAnnotation(this.sketch.id, 'comment', comment, [this.event], this.currentSearchNode)
        .then((response) => {
          this.comments.splice(commentIndex, 1, comment)
          comment.editable = false
        })
        .catch((e) => {
          console.error(e)
        })
    },
    deleteComment: function (commentId, commentIndex) {
      if (confirm('Are you sure?')) {
        ApiClient.deleteEventAnnotation(this.sketch.id, 'comment', commentId, this.event, this.currentSearchNode)
          .then((response) => {
            this.comments.splice(commentIndex, 1)
          })
          .catch((e) => {
            console.error(e)
          })
      }
    },
    editComment(commentIndex, enable = true) {
      const changeComment = this.comments[commentIndex]
      changeComment.editable = enable
      this.comments.splice(commentIndex, 1, changeComment)
    },
    selectComment(comment) {
      this.selectedComment = comment
    },
    unSelectComment() {
      this.selectedComment = false
    },
    copyEventUrlToClipboard() {
      let eventUrl = window.location.origin + this.$route.path + '?q=_id:' + this.event._id
      navigator.clipboard.writeText(eventUrl)
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
    copyEventAsJSON() {
      let eventJSON = JSON.stringify(this.fullEvent, null, 3)
      navigator.clipboard.writeText(eventJSON)
    },
    searchContext: function (event) {
      // TODO: not yet implemented
    },
    contextLinkRedirect(key, item, value) {
      const fieldConfList = this.contextLinkConf[key.toLowerCase()] ? this.contextLinkConf[key.toLowerCase()] : []
      for (const confItem of fieldConfList) {
        if (confItem['short_name'] === item) {
          if (confItem['redirect_warning']) {
            this.redirectWarnDialog = true
            this.contextValue = value
            this.contextUrl = confItem['context_link'].replace('<ATTR_VALUE>', encodeURIComponent(value))
          } else {
            // TODO verify if encodeURIComponent is sufficient sanitization here?
            window.open(confItem['context_link'].replace('<ATTR_VALUE>', encodeURIComponent(value)), '_blank')
            this.redirectWarnDialog = false
          }
        }
      }
    },
    getContextLinkRedirectState(key, item) {
      const fieldConfList = this.contextLinkConf[key.toLowerCase()] ? this.contextLinkConf[key.toLowerCase()] : []
      for (const confItem of fieldConfList) {
        if (confItem['short_name'] === item) {
          return confItem['redirect_warning']
        }
      }
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
