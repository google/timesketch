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
            <h5><b>{{ deltaDays }}</b><br>days</h5>
          </div>
          <div class="ts-time-bubble-vertical-line ts-time-bubble-vertical-line-color"></div>
        </td>
      </tr>

      <!-- The event -->
      <tr class="ts-shadow-on-hover">

        <!-- Timeline color (set the color for the timeline) -->
        <td v-bind:style="timelineColor">
          {{ event._source.timestamp | formatTimestamp | moment("utc", datetimeFormat) }}
        </td>

        <!-- Action column -->
        <td>
          <div class="field is-grouped">
            <span v-if="displayControls" class="control">
              <input type="checkbox" :checked="isSelected" v-on:click="toggleSelect">
            </span>
            <span class="icon control" v-on:click="toggleStar" style="margin-right: 3px; cursor: pointer;">
              <i class="fas fa-star" v-if="isStarred" style="color: #ffe300; -webkit-text-stroke-width: 1px; -webkit-text-stroke-color: #d1d1d1;"></i>
              <i class="fas fa-star" v-if="!isStarred" style="color: #d3d3d3;"></i>
            </span>
            <span v-if="displayControls" class="icon control" style="cursor: pointer;" v-on:click="searchContext">
              <i class="fas fa-search" style="color: #d3d3d3;"></i>
            </span>
          </div>
        </td>

        <!-- Dynamic columns based on selected fields -->
        <td v-bind:style="fieldColumnColor" v-on:click="showDetail = !showDetail" style="cursor: pointer; max-width: 50ch;" v-for="(field, index) in selectedFields" :key="index">
          <span v-bind:class="{ 'ts-event-field-container': selectedFields.length === 1 }">
            <span v-bind:class="{ 'ts-event-field-ellipsis': selectedFields.length === 1 }">
              <span v-if="index === 0">
                <span v-if="displayOptions.showEmojis" v-for="emoji in event._source.__ts_emojis" :key="emoji" v-html="emoji" :title="meta.emojis[emoji]">{{ emoji }}</span>
                <span style="margin-left:10px;"></span>
                <span v-if="displayOptions.showTags" v-for="tag in event._source.tag" :key="tag" class="tag is-rounded" style="margin-right:5px;background:#d1d1d1;">{{ tag }}</span>
              </span>
              <span style="word-break: break-word;" :title="event._source[field.field]">
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
        <td colspan="5">
          <div style="max-width: 600px; border:1px solid #f5f5f5; border-radius: 4px; padding:10px; margin-bottom: 20px;">
            <article  class="media" v-for="comment in comments" :key="comment.created_at">
              <div class="media-content">
                <div class="content">
                  <p>
                    {{ comment.user.username }} <small style="margin-left: 10px;">{{ comment.created_at | moment("ll") }}</small>
                    <br>
                    {{ comment.comment }}
                  </p>
                </div>
              </div>
            </article>
          </div>
        </td>
      </tr>

      <!-- Event details that gets activated when the event row ic clicked -->
      <tr>
        <td colspan="5" style="padding: 0">
          <div v-if="showDetail" style="padding-top:20px; padding-bottom: 20px;">
            <div  class="field" style="max-width: 50%;">
              <p class="control">
                <textarea v-model="comment" required autofocus class="textarea" rows="1" placeholder="Add a comment ..."></textarea>
              </p>
            </div>
            <div class="field">
              <p class="control">
                <button class="button" v-on:click="postComment(comment)">Post comment</button>
              </p>
            </div>
            <ts-sketch-explore-event-list-row-detail :event="event" @addChip="$emit('addChip', $event)"></ts-sketch-explore-event-list-row-detail>
          </div>
        </td>
      </tr>

  </tbody>
</template>

<script>
  import ApiClient from '../../utils/RestApiClient'
  import TsSketchExploreEventListRowDetail from './EventListRowDetail'
  import EventBus from "../../main"

  export default {
  components: {
    TsSketchExploreEventListRowDetail
  },
  props: ['event', 'prevEvent', 'order', 'selectedFields', 'isRemoteSelected', 'displayOptions', 'displayControls'],
  data () {
    return {
      showDetail: false,
      isStarred: false,
      isSelected: false,
      isDarkTheme: false,
      comment: '',
      comments: []
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    },
    timelineColor () {
      let backgroundColor = this.timeline(this.event._index).color
      if (!backgroundColor.startsWith('#')) {
        backgroundColor = '#' + backgroundColor
      }
      if (this.isDarkTheme) {
        return {
          'background-color': backgroundColor,
          'filter': 'grayscale(25%)',
          'color': '#333'
        }
      }
      return {
        'background-color': backgroundColor
      }
    },
    fieldColumnColor () {
      let backgroundColor = '#f5f5f5'
      let fontColor = '#333'

      if (this.isDarkTheme) {
        backgroundColor = '#494949'
        fontColor = '#fafafa'
      }

      if (this.isStarred) {
        backgroundColor = '#fff4b3'
        fontColor = '#333'
      }

      if (this.isSelected) {
        backgroundColor = '#c3ecff'
        fontColor = '#333'
      }

      if (this.isDarkTheme) {
        return {
          'background-color': backgroundColor,
          'color': fontColor,
        }
      }
      return {
        'background-color': backgroundColor,
        'color': fontColor,
      }
    },
    datetimeFormat () {
      if (this.displayOptions.showMillis) {
        return 'YYYY-MM-DDTHH:mm:ss.SSSSSS'
      } else {
        return 'YYYY-MM-DDTHH:mm:ss'
      }
    },
    timelineName () {
      return this.timeline(this.event._index).name
    },
    deltaDays () {
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
    eventDataSparse () {
      let eventData = {}
      eventData['_index'] = this.event._index
      eventData['_id'] = this.event._id
      eventData['_type'] = this.event._type
      eventData['isSelected'] = this.isSelected
      return eventData
    }
  },
  methods: {
    timeline (indexName) {
      return this.sketch.timelines.find(function (timeline) {
        return timeline.searchindex.index_name === indexName
      })
    },
    toggleStar () {
      this.isStarred =! this.isStarred
      ApiClient.saveEventAnnotation(this.sketch.id, 'label', '__ts_star', this.event).then((response) => {
      }).catch((e) => {
        console.error(e)
      })
    },
    toggleStarOnSelect () {
      if (this.isSelected) {
        this.isStarred =! this.isStarred
      }
    },
    postComment: function (comment) {
      ApiClient.saveEventAnnotation(this.sketch.id, 'comment', comment, [this.event]).then((response) => {
        this.comments.push(response.data.objects[0][0])
        this.comment = ''
      }).catch((e) => {})
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
      this.isDarkTheme =! this.isDarkTheme
    }
  },
  beforeDestroy () {
    EventBus.$off('selectEvent', this.selectEvent)
    EventBus.$off('clearSelectedEvents', this.unSelectEvent)
    EventBus.$off('toggleStar', this.toggleStarOnSelect)
  },
  created () {
    EventBus.$on('selectEvent', this.selectEvent)
    EventBus.$on('clearSelectedEvents', this.unSelectEvent)
    EventBus.$on('toggleStar', this.toggleStarOnSelect)
    EventBus.$on('isDarkTheme', this.toggleTheme)

    this.isDarkTheme = localStorage.theme === 'dark';

    if (this.event._source.label.indexOf('__ts_star') > -1) {
        this.isStarred = true
    }
    if (this.event._source.label.indexOf('__ts_comment') > -1) {
        let searchindexId = this.event._index
        let eventId = this.event._id
        ApiClient.getEvent(this.sketch.id, searchindexId, eventId).then((response) => {
          this.comments = response.data.meta.comments
        }).catch((e) => {})
    }
  }
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
  width:100%;
  top: 0;
  left: 0;
}

.ts-timeline-name-column {
  font-size: 0.8em;
  font-weight: bold;
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
  opacity:0.999999;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 2px 6px rgba(0,0,0,0.24);
}

</style>
