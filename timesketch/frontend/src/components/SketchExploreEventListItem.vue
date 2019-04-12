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
    <table class="ts-event-list-table">
      <tbody>
        <tr>
          <td style="width:215px;" class="ts-event-table-column" v-bind:style="{ 'background-color': '#' + timelineColor }">
            {{ event._source.datetime }}
          </td>
          <!-- TODO: Add options here.
          <td style="width:200px;" class="ts-event-table-column ts-event-message-column"></td>
          -->
          <td style="width:100%;" class="ts-event-table-column ts-event-message-column" v-on:click="showDetail = !showDetail" >
            <span class="ts-event-message-container">
              <span class="ts-event-message-ellipsis" v-bind:title="event._source.message">
                <span v-for="emoji in event._source.__ts_emojis" :key="emoji" v-html="emoji">{{ emoji }}</span>
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
        <ts-sketch-explore-event-list-item-detail :event="event"></ts-sketch-explore-event-list-item-detail>
      </div>
    </div>
  </div>
</template>

<script>
import TsSketchExploreEventListItemDetail from './SketchExploreEventListItemDetail'

export default {
  name: 'ts-sketch-explore-event-list-item',
  props: ['event'],
  components: {
    TsSketchExploreEventListItemDetail
  },
  data () {
    return {
      showDetail: false
    }
  },
  methods: {
    timeline (indexName) {
      return this.sketch.timelines.find(function (timeline) {
        return timeline.searchindex.index_name === indexName
      })
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
      return this.timeline(this.event._index).color
    },
    timelineName () {
      return this.timeline(this.event._index).name
    }
  }
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
</style>
