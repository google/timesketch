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
  <div>

    <div v-if="deltaDays > 0">
      <div class="time-bubble-vertical-line"></div>
      <div class="time-bubble">
        <h5><b>{{ deltaDays }}</b><br>days</h5>
      </div>
      <div class="time-bubble-vertical-line"></div>
    </div>

    <table class="ts-event-list-table">
      <tbody>
        <tr>
          <td style="width:215px;" class="ts-event-table-column" v-bind:style="timelineColor">
            {{ event._source.datetime }}
          </td>
          <!-- TODO: Add options here.
          <td style="width:200px;" class="ts-event-table-column ts-event-message-column"></td>
          -->
          <td style="width:100%;" class="ts-event-table-column ts-event-message-column" v-on:click="showDetail = !showDetail" >
            <span class="ts-event-message-container">
              <span class="ts-event-message-ellipsis" v-bind:title="event._source.message">
                <span v-for="emoji in event._source.__ts_emojis" :key="emoji" v-html="emoji">{{ emoji }}</span>
                <span style="margin-left:10px;"></span>
                <span v-for="tag in event._source.tag" :key="tag" class="tag is-rounded" style="margin-right:5px;background:#d1d1d1;">{{ tag }}</span>
                {{ event._source.message }}
              </span>
            </span>
          </td>
          <td style="width:150px;" class="ts-event-table-column ts-timeline-name-column">
            {{ timelineName }}
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Detailed view -->
    <div v-if="showDetail">
      <div style="margin:10px 0 10px 0;background:#f9f9f9; border:none;border-radius:5px;padding:15px">
        <ts-sketch-explore-event-list-item-detail :event="event" @addChip="$emit('addChip', $event)"></ts-sketch-explore-event-list-item-detail>
      </div>
    </div>
  </div>
</template>

<script>
import TsSketchExploreEventListItemDetail from './EventListItemDetail'

export default {
  components: {
    TsSketchExploreEventListItemDetail
  },
  props: ['event', 'prevEvent'],
  data () {
    return {
      showDetail: false
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
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
      let deltaDays = delta / 60 / 60 / 24
      return Math.floor(deltaDays)
    }
  },
  methods: {
    timeline (indexName) {
      return this.sketch.timelines.find(function (timeline) {
        return timeline.searchindex.index_name === indexName
      })
    }
  },
}
</script>

<style lang="scss">

.ts-event-table-column {
  padding: 10px;
}

.ts-event-message-container {
  position: relative;
  max-width: 100%;
  padding: 0 !important;
  display: -webkit-flex;
  display: -moz-flex;
  display: flex;
  vertical-align: text-bottom !important;
}

.ts-event-message-column {
  background-color: #F5F5F5;
  cursor: pointer;
}

.ts-event-message-ellipsis {
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

.ts-event-message-container:after {
    content: '-';
    display: inline;
    visibility: hidden;
    width: 0;
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

.ts-event-list-table {
  width:100%;
  border-collapse:separate;
  border-spacing:1px;
  table-layout: fixed;
}

.time-bubble {
  width: 60px;
  height: 60px;
  background: #f5f5f5;
  border-radius: 30px;
  position: relative;
  margin: 0 0 0 70px;
  text-align: center;
}

.time-bubble h5 {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  margin: 0;
  color: #666;
}

.time-bubble-vertical-line {
  width: 2px;
  height: 20px;
  background: #f5f5f5;
  margin: 0 0 0 100px;
}
</style>
