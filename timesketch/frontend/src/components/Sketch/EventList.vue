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
  <table class="table is-fullwidth">
    <thead>
      <th :width="datetimeWidth">Datetime (UTC)</th>
      <th width="1">
        <span class="control">
          <input type="checkbox" v-on:click="toggleSelectAll">
        </span>
      </th>
      <th v-for="(field, index) in selectedFields" :key="index">{{ field.field | capitalize }}</th>
      <th width="150">Timeline name</th>
    </thead>
    <ts-sketch-explore-event-list-row v-for="(event, index) in eventList"
                                      :key="index"
                                      :event="event"
                                      :prevEvent="eventList[index - 1]"
                                      :order="order"
                                      :selected-fields="selectedFields"
                                      :display-options="displayOptions"
                                      :display-controls="true"
                                      v-bind:id="event._id"
                                      @addChip="$emit('addChip', $event)"
                                      @addLabel="$emit('addLabel', $event)"
                                      @searchContext="$emit('searchContext', $event)">
    </ts-sketch-explore-event-list-row>
  </table>
</template>

<script>
import TsSketchExploreEventListRow from './EventListRow'
import EventBus from "../../main"

export default {
  components: { TsSketchExploreEventListRow },
  props: ['eventList', 'order', 'selectedFields', 'displayOptions'],
  data () {
    return {
      selectAll: false
    }
  },
  methods: {
    toggleSelectAll: function () {
      if (this.selectAll) {
        EventBus.$emit('clearSelectedEvents')
        this.selectAll = false
      } else {
        EventBus.$emit('selectEvent')
        this.selectAll = true
      }
    }
  },
  computed: {
    datetimeWidth () {
      if (this.displayOptions.showMillis) {
        return '220'
      } else {
        return '165'
      }
    }
  }
}
</script>

<style lang="scss" scoped>

.table thead th {
  border:0;
}

</style>
