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
    <div class="field is-horizontal">
      <div class="field-body">

        <div class="field">
          <p class="control">
            <input class="input" ref="startInput" v-model="startDateTime" type="text" placeholder="2019-07-07T10:00:01" v-on:keyup.enter="formatDateTime()" v-on:blur="endDateTime || formatDateTime()">
          </p>
        </div>

        <span style="margin-right:10px;padding-top:5px;">&rarr;</span>

        <div class="field">
          <p class="control">
            <input class="input" ref="endInput" v-model="endDateTime" type="text" placeholder="2019-07-07T10:00:01" v-on:keyup.enter="selectedChip ? update() : submit()">
          </p>
        </div>
      </div>
    </div>

    <div class="field is-horizontal">
        <div class="field is-grouped">
          <p class="control">
            <a :disabled="!startDateTime" class="button is-light" v-on:click="formatDateTime()">
              <span class="icon is-small">
                <i class="fas fa-magic"></i>
              </span>
              <span>Format</span>
            </a>
          </p>
          <p class="control">
            <button v-if="selectedChip" :disabled="!(startDateTime && endDateTime)" class="button is-success is-outlined" v-on:click="update">Update</button>
            <button v-else :disabled="!(startDateTime && endDateTime)" class="button is-success is-outlined" v-on:click="submit">+ Add time range</button>
          </p>
        </div>
    </div>

  </div>
</template>

<script>
export default {
  props: ['start', 'end', 'selectedChip'],
  data () {
    return {
      startDateTime: this.start,
      endDateTime: this.end,
      chip: this.selectedChip
    }
  },
  methods: {
    formatDateTime: function () {
      const startDateTimeString = this.startDateTime
      let endDateTimeString = ''
      let dateTimeTemplate = 'YYYY-MM-DDTHH:mm:ss'

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
          this.startDateTime = startDateTimeMoment.format(dateTimeTemplate)
          this.endDateTime = startDateTimeMoment.add(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
        }
        if (startDateTimeOffset === '-') {
          this.startDateTime = startDateTimeMoment.subtract(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
          this.endDateTime = startDateTimeMoment.format(dateTimeTemplate)
        }
        if (startDateTimeOffset === '-+' || startDateTimeOffset === '+-') {
          this.startDateTime = startDateTimeMoment.subtract(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
          this.endDateTime = startDateTimeMoment.add(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
        }
        return
      }

      if (!endDateTimeString) {
        endDateTimeString = startDateTimeString
      }

      // Fall back to user input
      let startDateTimeMoment = this.$moment.utc(startDateTimeString)
      let endDateTimeMoment = this.$moment.utc(endDateTimeString)

      if (!startDateTimeMoment.hour() && !startDateTimeMoment.minute() && !startDateTimeMoment.second()) {
          dateTimeTemplate = 'YYYY-MM-DD'
      }

      this.startDateTime = startDateTimeMoment.format(dateTimeTemplate)
      this.endDateTime = endDateTimeMoment.format(dateTimeTemplate)

      // Move cursor to the End Time form input
      this.$refs.endInput.focus()

    },
    submit: function () {
      if (!(this.startDateTime && this.endDateTime)) {
        return
      }

      // The filter doesn't work if the start date is after the end date
      if (this.startDateTime > this.endDateTime) {
        [this.startDateTime, this.endDateTime] = [this.endDateTime, this.startDateTime]
      }

      this.chip = {
          'field': '',
          'value': this.startDateTime + ',' + this.endDateTime,
          'type': 'datetime_range',
          'operator': 'must'
        }
      this.$emit('addChip', this.chip)
      this.startDateTime = ''
      this.endDateTime = ''

      // Close the menu
      this.$emit('hideDropdown')
    },
    update: function() {
      if (!(this.startDateTime && this.endDateTime)) {
        return
      }

      // The filter doesn't work if the start date is after the end date
      if (this.startDateTime > this.endDateTime) {
        [this.startDateTime, this.endDateTime] = [this.endDateTime, this.startDateTime]
      }

      this.chip['value'] = this.startDateTime + ',' + this.endDateTime;
      this.$emit('updateChip', this.chip)

      // Close the menu
      this.$emit('hideDropdown')
    }
  }
}
</script>
