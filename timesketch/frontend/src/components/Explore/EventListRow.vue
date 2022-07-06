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
  <tbody>
    <!-- Time bubbles -->
    <tr v-if="deltaDays > 0">
      <td colspan="5" style="padding: 0">
        <div class="ts-time-bubble-vertical-line ts-time-bubble-vertical-line-color"></div>
        <div class="ts-time-bubble ts-time-bubble-color">
          <h5>
            <b>{{ deltaDays | compactNumber }}</b
            ><br />days
          </h5>
        </div>
        <div class="ts-time-bubble-vertical-line ts-time-bubble-vertical-line-color"></div>
      </td>
    </tr>

    <!-- The event -->
    <tr>
      <!-- Timeline color (set the color for the timeline) -->
      <td v-bind:style="timelineColor">
        {{ event._source.timestamp | formatTimestamp | moment('utc', datetimeFormat) }}
      </td>

      <!-- Action column -->
      <td>
        <div class="field is-grouped">
          <span v-if="displayControls" class="control">
            <input type="checkbox" :checked="isSelected" v-on:click="toggleSelect" />
          </span>
          <span class="icon control" v-on:click="toggleStar" style="margin-right: 3px; cursor: pointer">
            <i
              class="fas fa-star"
              v-if="isStarred"
              title="Unstar the event"
              style="color: #ffe300; -webkit-text-stroke-width: 1px; -webkit-text-stroke-color: #d1d1d1"
            ></i>
            <i class="fas fa-star" v-if="!isStarred" title="Star the event" style="color: #d3d3d3"></i>
          </span>
          <span
            v-if="displayControls"
            class="icon control"
            style="margin-right: 3px; cursor: pointer"
            v-on:click="searchContext"
          >
            <i class="fas fa-search" title="Search +/- 5min" style="color: #d3d3d3"></i>
          </span>
          <span class="icon control">
            <ts-dropdown>
              <template v-slot:dropdown-trigger-element>
                <i class="fas fa-tag" title="Labels" style="color: #d3d3d3" slot="trigger"></i>
              </template>

              <span v-if="filteredLabelsToAdd.length">
                <b>Add label</b>
                <br /><br />
                <div class="level" style="margin-bottom: 5px" v-for="label in filteredLabelsToAdd" :key="label.label">
                  <div class="level-left">
                    <div class="field">
                      <b-checkbox type="is-info" v-model="selectedLabels" :native-value="label.label">
                        {{ label.label }}
                      </b-checkbox>
                    </div>
                  </div>
                </div>
              </span>

              <span v-if="event._source.label.length">
                <i class="fas fa-trash" style="margin-right: 7px"></i>
                <b>Remove label</b>
                <br /><br />
                <div class="level" style="margin-bottom: 5px" v-for="label in event._source.label" :key="label">
                  <div class="level-left">
                    <div class="field">
                      <b-checkbox type="is-danger" v-model="labelsToRemove" :native-value="label">
                        {{ label }}
                      </b-checkbox>
                    </div>
                  </div>
                </div>
              </span>

              <br />
              <b>Create and add a new label</b>
              <div class="field is-grouped" style="padding-top: 10px">
                <p class="control is-expanded">
                  <input class="input" v-model="labelToAdd" placeholder="New label" />
                </p>
                <p class="control">
                  <button v-on:click="addLabels(labelToAdd)" class="button">Save</button>
                </p>
              </div>
              <button
                v-if="selectedLabels.length || labelsToRemove.length"
                class="button is-info"
                v-on:click="addLabels()"
                :disabled="labelToAdd !== null && labelToAdd !== ''"
              >
                Apply
              </button>
            </ts-dropdown>
          </span>
        </div>
      </td>

      <!-- Dynamic columns based on selected fields -->
      <td
        v-bind:style="fieldColumnColor"
        v-on:click="showDetail = !showDetail"
        style="cursor: pointer; max-width: 50ch"
        class="ts-event-list-row-background-color"
        v-for="(field, index) in selectedFields"
        :key="index"
      >
        <span v-bind:class="{ 'ts-event-field-container': selectedFields.length === 1 }">
          <span v-bind:class="{ 'ts-event-field-ellipsis': selectedFields.length === 1 }">
            <!-- eslint-disable vue/no-use-v-if-with-v-for -->
            <span v-if="index === 0">
              <span
                v-if="displayOptions.showEmojis"
                v-for="emoji in event._source.__ts_emojis"
                :key="emoji"
                v-html="emoji"
                :title="meta.emojis[emoji]"
                >{{ emoji }}</span
              >
              <span style="margin-left: 10px"></span>
              <span
                v-if="displayOptions.showTags"
                v-for="tag in event._source.tag"
                :key="tag"
                class="tag is-small"
                style="margin-right: 5px; background-color: var(--tag-background-color); color: var(--tag-font-color)"
                >{{ tag }}</span
              >
              <span
                v-if="displayOptions.showTags"
                v-for="label in filteredLabels"
                :key="label"
                class="tag is-small"
                style="margin-right: 5px; background-color: var(--tag-background-color); color: var(--tag-font-color)"
                >{{ label }}</span
              >
            </span>
            <!--eslint-enable-->
            <span style="word-break: break-word" :title="event._source[field.field]">
              {{ event._source[field.field] }}
            </span>
          </span>
        </span>
      </td>

      <!-- Timeline name -->
      <td class="ts-timeline-name-column ts-timeline-name-column-color">
        <span :title="timelineName">
          {{ timelineName }}
        </span>
      </td>
    </tr>

    <!-- Comments row -->
    <tr v-if="comments.length">
      <td colspan="5" style="padding: 0">
        <div style="max-width: 100%; border: 1px solid #f5f5f5; border-radius: 4px; padding: 10px; margin-bottom: 20px">
          <article class="field" v-for="(comment, index) in comments" :key="comment.id">
            <small style="margin-right: 10px">{{ comment.updated_at | moment('utc', 'YYYY-MM-DD HH:mm:ss') }}</small>
            <small style="margin-right: 10px">{{ comment.user.username }}</small>
            <br />
            <div v-if="comment && comment.editable" class="media-content">
              <div class="field" style="max-width: 50%">
                <p class="control">
                  <textarea v-model="comments[index].comment" required autofocus class="textarea" rows="1"></textarea>
                </p>
              </div>
              <div class="field">
                <p class="control">
                  <button
                    class="button is-small is-rounded"
                    style="margin-right: 0.75rem"
                    v-on:click="updateComment(comment, index)"
                  >
                    Save
                  </button>

                  <button
                    class="button is-small is-rounded"
                    style="margin-right: 0.75rem"
                    v-on:click="toggleEditComment(index, false)"
                  >
                    Cancel
                  </button>
                </p>
              </div>
            </div>
            <div v-if="comment && !comment.editable" class="media-content">
              <div class="level content">
                <div class="level-left">
                  {{ comment.comment }}
                </div>
                <div
                  v-if="meta.permissions.write && getCurrentUser() == comment.user.username"
                  class="level-right field"
                >
                  <button
                    class="button is-small is-rounded"
                    style="margin-right: 0.75rem"
                    v-on:click="toggleEditComment(index, true)"
                  >
                    Edit
                  </button>
                  <button
                    class="button is-small is-rounded is-danger"
                    style="margin-right: 0.75rem"
                    v-on:click="deleteComment(comment.id, index)"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          </article>
        </div>
      </td>
    </tr>

    <!-- Event details that gets activated when the event row is clicked -->
    <tr>
      <td colspan="5" style="padding: 0">
        <div v-if="showDetail" style="padding-top: 20px; padding-bottom: 20px; padding-left: 10px">
          <div class="field" style="max-width: 50%">
            <p class="control">
              <textarea
                v-model="comment"
                required
                autofocus
                class="textarea"
                rows="1"
                placeholder="Add a comment ..."
              ></textarea>
            </p>
          </div>
          <div class="field">
            <p class="control">
              <button class="button is-small is-rounded" v-on:click="postComment(comment)">Post comment</button>
            </p>
          </div>
          <ts-sketch-explore-event-list-row-detail
            :event="event"
            @addChip="$emit('addChip', $event)"
          ></ts-sketch-explore-event-list-row-detail>
        </div>
      </td>
    </tr>
  </tbody>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsSketchExploreEventListRowDetail from './EventListRowDetail'
import TsDropdown from '../Common/Dropdown'
import EventBus from '../../main'
import { ToastProgrammatic as Toast } from 'buefy'

export default {
  components: {
    TsSketchExploreEventListRowDetail,
    TsDropdown,
  },
  props: [
    'event',
    'prevEvent',
    'order',
    'selectedFields',
    'isRemoteSelected',
    'displayOptions',
    'displayControls',
    'searchNode',
  ],
  data() {
    return {
      showDetail: false,
      isStarred: false,
      isSelected: false,
      isDarkTheme: false,
      comment: '',
      comments: [],
      labelToAdd: null,
      selectedLabels: [],
      labelsToRemove: [],
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    currentSearchNode() {
      return this.searchNode || this.$store.state.currentSearchNode
    },
    timelineColor() {
      let backgroundColor = this.timeline.color
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
      }
      if (this.isDarkTheme) {
        return {
          'background-color': backgroundColor,
          filter: 'grayscale(25%)',
          color: '#333',
        }
      }
      return {
        'background-color': backgroundColor,
      }
    },
    fieldColumnColor() {
      if (this.isSelected) {
        return {
          'background-color': '#c3ecff',
          color: '#333',
        }
      }

      if (this.isStarred) {
        return {
          'background-color': '#fff4b3',
          color: '#333',
        }
      }
      return {}
    },
    datetimeFormat() {
      if (this.displayOptions.showMillis) {
        return 'YYYY-MM-DDTHH:mm:ss.SSSSSS'
      } else {
        return 'YYYY-MM-DDTHH:mm:ss'
      }
    },
    timeline() {
      let isLegacy = this.meta.indices_metadata[this.event._index].is_legacy
      let timeline
      if (isLegacy) {
        timeline = this.sketch.active_timelines.filter(
          (timeline) => timeline.searchindex.index_name === this.event._index
        )[0]
      } else {
        timeline = this.sketch.active_timelines.filter(
          (timeline) => timeline.id === this.event._source.__ts_timeline_id
        )[0]
      }
      return timeline
    },
    timelineName() {
      return this.timeline.name
    },
    deltaDays() {
      if (!this.prevEvent) {
        return 0
      }
      let timestampMillis = this.$options.filters.formatTimestamp(this.event._source.timestamp)
      let prevTimestampMillis = this.$options.filters.formatTimestamp(this.prevEvent._source.timestamp)
      let timestamp = Math.floor(timestampMillis / 1000)
      let prevTimestamp = Math.floor(prevTimestampMillis / 1000)
      let delta = Math.floor(timestamp - prevTimestamp)
      if (this.order === 'desc') {
        delta = Math.floor(prevTimestamp - timestamp)
      }
      let deltaDays = delta / 60 / 60 / 24
      return Math.floor(deltaDays)
    },
    eventDataSparse() {
      let eventData = {}
      eventData['_index'] = this.event._index
      eventData['_id'] = this.event._id
      eventData['_type'] = this.event._type
      eventData['isSelected'] = this.isSelected
      eventData['isStarred'] = this.isStarred
      return eventData
    },
    filteredLabels() {
      return this.event._source.label.filter((label) => !label.startsWith('__'))
    },
    filteredLabelsToAdd() {
      return this.meta.filter_labels.filter((label) => this.event._source.label.indexOf(label.label) === -1)
    },
    filteredLabelsToRemove() {
      return this.meta.filter_labels.filter((label) => this.event._source.label.indexOf(label.label) !== -1)
    },
  },
  methods: {
    toggleStar() {
      if (!this.isStarred) {
        // Update the Search History to indicate that an entry was starred
        EventBus.$emit('eventAnnotated', { type: '__ts_star', event: this.event, searchNode: this.currentSearchNode })
      }
      this.isStarred = !this.isStarred
      ApiClient.saveEventAnnotation(this.sketch.id, 'label', '__ts_star', this.event, this.currentSearchNode)
        .then((response) => {})
        .catch((e) => {
          console.error(e)
        })
    },
    toggleStarOnSelect(eventsToToggle) {
      // The 'includes' check is there to avoid toggling all the selected events
      if (this.isSelected && eventsToToggle.includes(this.event._id)) {
        this.isStarred = !this.isStarred
      }
    },
    postComment: function (comment) {
      EventBus.$emit('eventAnnotated', { type: '__ts_comment', event: this.event, searchNode: this.currentSearchNode })
      ApiClient.saveEventAnnotation(this.sketch.id, 'comment', comment, [this.event], this.currentSearchNode)
        .then((response) => {
          this.comments.push(response.data.objects[0][0])
          this.comment = ''
        })
        .catch((e) => {})
    },
    updateComment: function (comment, commentIndex) {
      ApiClient.updateEventAnnotation(this.sketch.id, 'comment', comment, [this.event], this.currentSearchNode)
        .then((response) => {
          this.$set(this.comments, commentIndex, response.data.objects[0][0])
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
    toggleEditComment(commentIndex, enable) {
      if (enable) {
        const changeComment = this.comments[commentIndex]
        changeComment.editable = true
        this.$set(this.comments, commentIndex, changeComment)
      } else {
        const changeComment = this.comments[commentIndex]
        changeComment.editable = false
        this.$set(this.comments, commentIndex, changeComment)
      }
    },
    getCurrentUser() {
      if (this.$store.state.currentUser) {
        this.currentUser = this.$store.state.currentUser
      } else if (!this.currentUser) {
        ApiClient.getLoggedInUser().then((response) => {
          this.currentUser = response.data.objects[0].username
        })
      }
      return this.currentUser
    },
    addLabels: function (labels) {
      if (labels === undefined) {
        labels = this.selectedLabels
      }
      if (!Array.isArray(labels)) {
        labels = [labels]
      }

      if (labels.length) {
        EventBus.$emit('eventAnnotated', { type: '__ts_label', event: this.event, searchNode: this.currentSearchNode })
      }

      labels.forEach((label) => {
        if (this.event._source.label.indexOf(label) === -1) {
          this.event._source.label.push(label)
          ApiClient.saveEventAnnotation(this.sketch.id, 'label', label, [this.event], this.currentSearchNode)
            .then((response) => {
              this.$emit('addLabel', label)
            })
            .catch((e) => {
              Toast.open('Error adding label')
              this.event._source.label = this.event._source.label.filter((e) => e !== label)
            })
        }
      })

      if (this.labelsToRemove.length) {
        this.labelsToRemove.forEach((label) => {
          ApiClient.saveEventAnnotation(this.sketch.id, 'label', label, [this.event], this.currentSearchNode, true)
            .then((response) => {})
            .catch((e) => {})
          this.event._source.label = this.event._source.label.filter((e) => e !== label)
        })
        this.labelsToRemove = []
      }

      this.selectedLabels = []
      this.labelToAdd = null
      this.$refs.labelDropdown.toggle()
    },
    searchContext: function () {
      this.$emit('searchContext', this.event)
    },
    selectEvent: function () {
      this.isSelected = true
      EventBus.$emit('eventSelected', this.eventDataSparse)
    },
    unSelectEvent: function () {
      this.isSelected = false
      EventBus.$emit('eventSelected', this.eventDataSparse)
    },
    toggleSelect: function () {
      if (this.isSelected) {
        this.unSelectEvent()
      } else {
        this.selectEvent()
      }
    },
    toggleTheme: function () {
      this.isDarkTheme = !this.isDarkTheme
    },
  },
  beforeDestroy() {
    EventBus.$off('selectEvent', this.selectEvent)
    EventBus.$off('clearSelectedEvents', this.unSelectEvent)
    EventBus.$off('toggleStar', this.toggleStarOnSelect)
  },
  created() {
    EventBus.$on('selectEvent', this.selectEvent)
    EventBus.$on('clearSelectedEvents', this.unSelectEvent)
    EventBus.$on('toggleStar', this.toggleStarOnSelect)
    EventBus.$on('isDarkTheme', this.toggleTheme)

    /*
    let isLegacy = this.meta.indices_metadata[this.event._index].is_legacy
    if (isLegacy) {
      this.timeline = this.sketch.active_timelines.filter(
        timeline => timeline.searchindex.index_name === this.event._index
      )[0]
    } else {
      this.timeline = this.sketch.active_timelines.filter(
        timeline => timeline.id === this.event._source.__ts_timeline_id
      )[0]
    }
    */

    this.isDarkTheme = localStorage.theme === 'dark'

    if (this.event._source.label.indexOf('__ts_star') > -1) {
      this.isStarred = true
    }
    if (this.event._source.label.indexOf('__ts_comment') > -1) {
      let searchindexId = this.event._index
      let eventId = this.event._id
      ApiClient.getEvent(this.sketch.id, searchindexId, eventId)
        .then((response) => {
          this.comments = response.data.meta.comments
        })
        .catch((e) => {})
    }
  },
}
</script>

<style lang="scss" scoped>
.ts-event-field-container {
  position: relative;
  max-width: 100%;
  padding: 0 !important;
  display: -webkit-flex;
  display: -moz-flex;
  display: flex;
  vertical-align: text-bottom !important;
}

.ts-event-field-container:after {
  content: '-';
  display: inline;
  visibility: hidden;
  width: 0;
}

.ts-event-field-ellipsis {
  position: absolute;
  white-space: nowrap;
  overflow-y: visible;
  overflow-x: hidden;
  text-overflow: ellipsis;
  -ms-text-overflow: ellipsis;
  -o-text-overflow: ellipsis;
  max-width: 100%;
  min-width: 0;
  width: 100%;
  top: 0;
  left: 0;
}

.ts-timeline-name-column {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
  max-width: 150px;
  word-wrap: break-word;
}

.ts-time-bubble {
  width: 60px;
  height: 60px;
  border-radius: 30px;
  position: relative;
  margin: 0 0 0 45px;
  text-align: center;
  font-size: var(--font-size-small);
}

.ts-time-bubble h5 {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  margin: 0;
}

.ts-time-bubble-vertical-line {
  width: 2px;
  height: 20px;
  margin: 0 0 0 75px;
}

.ts-shadow-on-hover:hover {
  opacity: 0.999999;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.24);
}
</style>
