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
          <div class="ts-time-bubble-vertical-line"></div>
          <div class="ts-time-bubble">
            <h5><b>{{ deltaDays }}</b><br>days</h5>
          </div>
          <div class="ts-time-bubble-vertical-line"></div>
        </td>
      </tr>

      <!-- The event -->
      <tr class="ts-shadow-on-hover">

        <!-- Timeline color (set the color for the timeline) -->
        <td v-bind:style="timelineColor">
          {{ event._source.datetime | moment("YYYY-MM-DDTHH:mm:ss.SSSSSS") }}
        </td>

        <!-- Action column -->
        <td>
          <div class="field is-grouped">
            <span class="control">
              <input type="checkbox" :checked="isSelected" v-on:click="toggleSelect">
            </span>
            <span class="icon control" v-on:click="toggleStar" style="margin-right: 3px; cursor: pointer;">
              <i class="fas fa-star" v-if="isStarred" style="color: #ffe300; -webkit-text-stroke-width: 1px; -webkit-text-stroke-color: #d1d1d1;"></i>
              <i class="fas fa-star" v-if="!isStarred" style="color: #d3d3d3;"></i>
            </span>
            <span class="icon control" style="cursor: pointer;" v-on:click="searchContext">
              <i class="fas fa-search" style="color: #d3d3d3;"></i>
            </span>
          </div>
        </td>

        <!-- Dynamic columns based on selected fields -->
        <td v-bind:style="messageFieldColor" v-on:click="showDetail = !showDetail" style="cursor: pointer;" v-for="(field, index) in selectedFields" :key="index">
          <span class="ts-event-field-container">
            <span class="ts-event-field-ellipsis">
              <span v-if="index === 0">
                <span v-for="emoji in event._source.__ts_emojis" :key="emoji" v-html="emoji" :title="meta.emojis[emoji]">{{ emoji }}</span>
                <span style="margin-left:10px;"></span>
                <span v-for="tag in event._source.tag" :key="tag" class="tag is-rounded" style="margin-right:5px;background:#d1d1d1;">{{ tag }}</span>
              </span>
              <span :title="event._source[field.field]">
                {{ event._source[field.field] }}
              </span>
            </span>
          </span>
        </td>

        <!-- Timeline name -->
        <td class="ts-timeline-name-column">
          <span>
            {{ timelineName }}
          </span>
        </td>

      </tr>

      <!-- Comments row -->
      <tr v-if="comments.length">
        <td colspan="5">
          <div style="max-width: 600px; border:1px solid #f5f5f5; border-radius: 4px; padding:10px; margin-bottom: 20px;">
            <article  class="media" v-for="comment in comments" :key="comment.created_at">
              <figure class="media-left">
                <div class="ts-avatar-circle"></div>
              </figure>
              <div class="media-content">
                <div class="content">
                  <p>
                    <strong>{{ comment.user.username }}</strong> <small style="margin-left: 10px;">{{ comment.created_at | moment("ll") }}</small>
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
  props: ['event', 'prevEvent', 'order', 'selectedFields', 'isRemoteSelected'],
  data () {
    return {
      showDetail: false,
      isStarred: false,
      isSelected: false,
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
      let hexColor = this.timeline(this.event._index).color
      if (!hexColor.startsWith('#')) {
        hexColor = '#' + hexColor
      }
      return {
        'background-color': hexColor
      }
    },
    messageFieldColor () {
      let hexColor = '#f5f5f5'
      if (this.isStarred) {
        hexColor = '#fff4b3'
      }
      if (this.isSelected) {
        hexColor = '#c3ecff'
      }
      return {
        'background-color': hexColor
      }
    },
    timelineName () {
      return this.timeline(this.event._index).name
    },
    deltaDays () {
      if (!this.prevEvent) {
        return 0
      }
      let timestamp = Math.floor(this.event._source.timestamp / 1000000)
      let prevTimestamp = Math.floor(this.prevEvent._source.timestamp / 1000000)
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

.ts-event-field-column {
  background-color: #F5F5F5;
  cursor: pointer;
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
  background: #f1f1f1;
  font-size: 0.8em;
  font-weight: bold;
  color: #999999;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
  word-wrap: break-word;
}

.ts-time-bubble {
  width: 60px;
  height: 60px;
  background: #f5f5f5;
  border-radius: 30px;
  position: relative;
  margin: 0 0 0 70px;
  text-align: center;
}

.ts-time-bubble h5 {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  margin: 0;
  color: #666;
}

.ts-time-bubble-vertical-line {
  width: 2px;
  height: 20px;
  background: #f5f5f5;
  margin: 0 0 0 100px;
}

.ts-shadow-on-hover:hover {
  opacity:0.999999;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 2px 6px rgba(0,0,0,0.24);
}

.ts-avatar-circle {
  width: 48px;
  height: 48px;
  background-color: #f5f5f5;
  border-radius: 50%;
  -webkit-border-radius: 50%;
  -moz-border-radius: 50%;
}

</style>
