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
  <form v-on:submit.prevent="formatDateTime">
    <div class="field is-horizontal">
      <div class="field-body">
        <div class="field">
          <label class="label">Start</label>
          <p class="control is-expanded">
            <input class="input" v-model="startDateTime" type="text"
                   placeholder="2019-07-07T10:00:01">
          </p>
        </div>
        <div class="field">
          <label class="label">End</label>
          <p class="control is-expanded">
            <input class="input" v-model="endDateTime" type="text"
                   placeholder="2019-07-07T10:00:01">
          </p>
        </div>
      </div>
    </div>
    <button class="button">Filter</button>
  </form>
</template>

<script>
export default {
  name: 'ts-sketch-explore-filter-time',
  data () {
    return {
      startDateTime: '',
      endDateTime: ''
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    },
    currentQueryFilter: {
      get: function () {
        return this.$store.state.currentQueryFilter
      },
      set: function (queryFilter) {
        this.$store.commit('updateCurrentQueryFilter', queryFilter)
      }
    }
  },
  methods: {
    formatDateTime: function () {
      const startDateTimeString = this.startDateTime
      const endDateTimeString = this.endDateTime
      const dateTimeTemplate = 'YYYY-MM-DDTHH:mm:ss'

      // Exit early if start time is missing
      if (startDateTimeString == null || startDateTimeString === '') {
        return
      }

      // Parse offset given by user. Eg. +-10m
      const offsetRegexp = /(.*?)(-|\+|\+-|-\+)(\d+)(y|d|h|m|s|M|Q|w|ms)/g
      const offsetRegexpMatch = offsetRegexp.exec(startDateTimeString)

      if (offsetRegexpMatch != null) {
        const startDateTimeMoment = this.$moment.utc(offsetRegexpMatch[1])
        const startDateTimeOffset = offsetRegexpMatch[2]
        const startDateTimeOffsetCount = offsetRegexpMatch[3]
        const startDateTimeOffsetInterval = offsetRegexpMatch[4] || 'm'

        // Calculate time range
        if (startDateTimeOffset === '+') {
          this.currentQueryFilter.time_start = startDateTimeMoment.format(dateTimeTemplate)
          this.currentQueryFilter.time_end = startDateTimeMoment.add(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
        }
        if (startDateTimeOffset === '-') {
          this.currentQueryFilter.time_start = startDateTimeMoment.subtract(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
          this.currentQueryFilter.time_end = startDateTimeMoment.format(dateTimeTemplate)
        }
        if (startDateTimeOffset === '-+' || startDateTimeOffset === '+-') {
          this.currentQueryFilter.time_start = startDateTimeMoment.subtract(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
          this.currentQueryFilter.time_end = startDateTimeMoment.add(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
        }
        this.startDateTime = this.currentQueryFilter.time_start
        this.endDateTime = this.currentQueryFilter.time_end
        return
      }

      // Fall back to user input
      let startDateTimeMoment = this.$moment.utc(startDateTimeString)
      let endDateTimeMoment = this.$moment.utc(endDateTimeString)
      this.currentQueryFilter.time_start = startDateTimeMoment.format(dateTimeTemplate)
      this.currentQueryFilter.time_end = endDateTimeMoment.format(dateTimeTemplate)

      this.startDateTime = this.currentQueryFilter.time_start
      this.endDateTime = this.currentQueryFilter.time_end
    }
  }
}
</script>

<style lang="scss"></style>
