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
    <!-- Time interval -->
    <div class="field is-horizontal">
      <div class="field-body" style="display:flex; align-items:center;">

        <b-radio v-model="radio" native-value="interval"></b-radio>
        <div class="field">
          <p class="control">
            <input class="input" ref="offsetStartInput" v-model.trim="offsetStart" type="text" :disabled="!isSelected('interval')" :placeholder="getPlaceholder('interval')"
            v-on:change="offsetStart && formatDateTime()" v-on:keyup.enter="submit()">
          </p>
        </div>
        <div>-</div>
        <div class="field" style="margin: 0px;">
          <p class="control" style="width: 40px; margin-left: 2px;">
            <input class="input" ref="offsetMinusInput" v-model.number="offsetMinus" type="text" style="width:90%;" :disabled="!isSelected('interval')"
            v-on:change="offsetMinus && formatDateTime()" v-on:keyup.enter="submit()" v-on:keyup.up="offsetMinus++" v-on:keyup.down="offsetMinus--">
          </p>
        </div>
        <div>+</div>
        <div class="field" style="margin: 0px;">
          <p class="control" style="width: 40px; margin-left: 2px;">
            <input class="input" ref="offsetPlusInput" v-model.number="offsetPlus" type="text" style="width:90%;" :disabled="!isSelected('interval')"
            v-on:change="offsetPlus && formatDateTime()" v-on:keyup.enter="submit()" v-on:keyup.up="offsetPlus++" v-on:keyup.down="offsetPlus--">
          </p>
        </div>
        <div> </div>
        <div class="field">
          <p class="control">
            <span class="select">
              <select v-model="selectedInterval" :disabled="!isSelected('interval')" v-on:change="offsetStart && formatDateTime()">
                <option v-for="option in intervals" :value="option.value" :key="option.value">{{ option.text }}</option>
              </select>
            </span>
          </p>
        </div>
      </div>
    </div>

    <!-- Time range -->
    <div class="field is-horizontal">
      <div class="field-body" style="display:flex; align-items:center;">

        <b-radio v-model="radio" native-value="range"></b-radio>
        <div class="field">
          <p class="control">
            <input class="input" ref="startInput" v-model.trim="startDateTime" type="text" :disabled="!isSelected('range')" :placeholder="getPlaceholder('range')"
            v-on:change="startDateTime && formatDateTime()" v-on:keyup.enter="endDateTime ? submit() : jumpTo('endInput')">
          </p>
        </div>

        <span style="margin-right:10px;">&rarr;</span>

        <div class="field">
          <p class="control">
            <input class="input" ref="endInput" v-model.trim="endDateTime" type="text" :disabled="!isSelected('range')" :placeholder="getPlaceholder('range')"
            v-on:change="endDateTime && formatDateTime()" v-on:keyup.enter="submit()">
          </p>
        </div>
      </div>
    </div>

    <!-- Submit button -->
    <div class="field is-horizontal">
      <div class="field is-grouped">
        <p class="control">
          <button :disabled="!hasAllInputs()" class="button is-success" v-on:click="submit">{{ selectedChip ? 'Update' : 'Create' }}</button>
        </p>
      </div>
    </div>

  </div>
</template>

<script>
export default {
  props: ['selectedChip'],
  data () {
    return {
      startDateTime: '',
      endDateTime: '',
      chip: this.selectedChip,
      radio: 'interval',
      offsetStart: '',
      offsetMinus: 5,
      offsetPlus: 5,
      intervals: [
        {'text': 'Second', 'value' : 's'},
        {'text': 'Minute', 'value' : 'm'},
        {'text': 'Hour', 'value': 'h'},
        {'text': 'Day', 'value': 'd'},
      ],
      selectedInterval: 'm',
    }
  },
  created: function () {
    if (!this.chip) {
      return
    }

    // Restoring values from the chip
    if (this.chip.type === 'datetime_range') {
      this.radio = 'range'
      let range = this.chip.value.split(',')
      this.startDateTime = range[0],
      this.endDateTime = range[1]
    }
    else {
      this.radio = 'interval'
      let offset = this.chip.value.split(' ')
      this.offsetStart = offset[0]
      this.offsetMinus = offset[1].match(/\d+/)[0]
      this.offsetPlus = offset[2].match(/\d+/)[0]
      this.selectedInterval = offset[1].match(/[a-zA-Z]+/)[0]
      this.formatDateTime()
    }
  },
  methods: {
    hasAllInputs: function () {
      if (this.isSelected('interval')) {
        if (this.offsetStart && this.offsetMinus && this.offsetPlus) {
          return true
        }
      }
      else if (this.isSelected('range')) {
        if (this.startDateTime && this.endDateTime){
          return true
        }
      }
      return false
    },
    getPlaceholder: function (radioName) {
      return (this.radio == radioName) ? '2019-07-07T10:00:01' : ''
    },
    getOffsetDateTime: function () {
       return `${this.offsetStart} -${this.offsetMinus}${this.selectedInterval} +${this.offsetPlus}${this.selectedInterval}`
    },
    formatDateTime: function () {
      // Exit early if user inputs are missing
      if (!this.hasAllInputs()) {
        return false
      }

      if (this.isSelected('interval')) {
        this.startDateTime = this.getOffsetDateTime()
      }

      let dateTimeTemplate = 'YYYY-MM-DDTHH:mm:ss'
      const startDateTimeString = this.startDateTime
      let endDateTimeString = this.endDateTime

      // Parse offset given by user. Eg. "2020-02-02 01:01:01 +10m -5m"
      const offsetRegexp = /^(.+?)[ ]?(-|\+|\+-|-\+)(\d+)(y|d|h|m|s|M|Q|w|ms)[ ]*(?:(-|\+|\+-|-\+)(\d+)(y|d|h|m|s|M|Q|w|ms))?$/
      let offsetRegexpMatch = offsetRegexp.exec(startDateTimeString)

      if (offsetRegexpMatch != null) {
        const startDateTimeMoment = this.$moment.utc(offsetRegexpMatch[1])
        this.startDateTime = startDateTimeMoment.format(dateTimeTemplate)
        this.endDateTime = startDateTimeMoment.format(dateTimeTemplate)
        if (!startDateTimeMoment.isValid()) {
          return false
        }

        offsetRegexpMatch = offsetRegexpMatch.slice(2) // To simplify the loop below we remove the first 2 entries (full match and the 1st match)
        while (offsetRegexpMatch.length) {
          let startDateTimeOffset = offsetRegexpMatch[0]
          let startDateTimeOffsetCount = offsetRegexpMatch[1]
          let startDateTimeOffsetInterval = offsetRegexpMatch[2] || 'm'
          offsetRegexpMatch = offsetRegexpMatch.slice(3)

          // Calculate time range
          // Warning: add() and subtract() mutate the object, hence we clone it first
          if (startDateTimeOffset === '+') {
            this.endDateTime = startDateTimeMoment.clone().add(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
          } else if (startDateTimeOffset === '-') {
            this.startDateTime = startDateTimeMoment.clone().subtract(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
          } else if (startDateTimeOffset === '-+' || startDateTimeOffset === '+-') {
            this.startDateTime = startDateTimeMoment.clone().subtract(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
            this.endDateTime = startDateTimeMoment.clone().add(startDateTimeOffsetCount, startDateTimeOffsetInterval).format(dateTimeTemplate)
          }
        }
        return true
      }

      // Fall back to user input
      if (!endDateTimeString) {
        endDateTimeString = startDateTimeString
      }

      let startDateTimeMoment = this.$moment.utc(startDateTimeString)
      let endDateTimeMoment = this.$moment.utc(endDateTimeString)

      if (!(startDateTimeMoment.hour() || startDateTimeMoment.minute() || startDateTimeMoment.second()
          || endDateTimeMoment.hour() || endDateTimeMoment.minute() || endDateTimeMoment.second())) {
          dateTimeTemplate = 'YYYY-MM-DD'
      }

      // Only overwrite the timestamp if it's valid
      if (startDateTimeMoment.isValid()) {
        this.startDateTime = startDateTimeMoment.format(dateTimeTemplate)
      }
      if (endDateTimeMoment.isValid()) {
        this.endDateTime = endDateTimeMoment.format(dateTimeTemplate)
      }

      // Terminate early if either of the timestamps is invalid
      if (!startDateTimeMoment.isValid() || !endDateTimeMoment.isValid()) {
        return false
      }

      return true
    },
    submit: function () {
      if (!(this.startDateTime && this.endDateTime && this.formatDateTime())) {
        return
      }

      // The filter doesn't work if the start date is after the end date
      if (this.startDateTime > this.endDateTime) {
        [this.startDateTime, this.endDateTime] = [this.endDateTime, this.startDateTime]
      }

      let chip_type = ''
      let chip_value = ''

      // Set the right chip type and value
      if (this.radio == 'interval') {
        chip_type = 'datetime_interval'
        chip_value = this.getOffsetDateTime()
      }
      else {
        chip_type = 'datetime_range'
        chip_value = this.startDateTime + ',' + this.endDateTime
      }

      // Update or creating a chip
      if (this.chip) {
        this.chip['type'] = chip_type
        this.chip['value'] = chip_value
        this.$emit('updateChip', this.chip)
      }
      else {
        this.chip = {
          'field': '',
          'type': chip_type,
          'value': chip_value,
          'operator': 'must',
          'active' : true
        }
        this.$emit('addChip', this.chip)

        // Wipe out the values in the Create drop down
        this.resetInterface()
      }

      // Close the menu
      this.$emit('hideDropdown')
    },
    resetInterface: function() {
      Object.assign(this.$data, this.$options.data()) // Credits to https://stackoverflow.com/a/38174780
    },
    isSelected: function(radioName) {
      return this.radio === radioName
    },
    jumpTo: function(name) {
      // Move cursor to the specified form input
      this.$refs[name].focus()
    }
  }
}
</script>
