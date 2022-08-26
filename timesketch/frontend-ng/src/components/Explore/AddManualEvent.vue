<!--
Copyright 2021 Google Inc. All rights reserved.

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
  <v-card width="700" style="overflow: visible">
    <v-container class="px-8">
      <br />
      <v-row>
        <v-col cols="6">
          <v-text-field
            :value="datetime"
            label="Datetime"
            outlined
            hide-details
            v-on:click="showPicker = true"
            v-model="datetime"
          >
          </v-text-field>
        </v-col>
      </v-row>

      <v-row v-if="showPicker">
        <v-col cols="12">
          <date-picker
            v-model="dateFromPicker"
            mode="dateTime"
            ref="picker"
            timezone="UTC"
            :is-dark="$vuetify.theme.dark"
            is24hr
            is-date
            is-expanded
          ></date-picker>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="6">
          <v-text-field :value="message" v-model="message" label="Message" outlined hide-details> </v-text-field>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="6">
          <v-text-field
            :value="timestampDesc"
            label="Timestamp Description"
            v-model="timestampDesc"
            outlined
            hide-details
          >
          </v-text-field>
        </v-col>
      </v-row>

      <v-row v-for="(attribute, index) in attributes" :key="index">
        <v-col cols="6">
          <v-text-field
            label="Attribute Name"
            outlined
            hide-details
            v-model="attributes[index].name"
            @change="setAddAttributeBtn(index)"
          >
          </v-text-field>
        </v-col>
        <v-col cols="6">
          <v-text-field
            label="Attribute Value"
            outlined
            hide-details
            v-model="attributes[index].value"
            @change="setAddAttributeBtn(index)"
          >
          </v-text-field>
        </v-col>
      </v-row>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text color="primary" @click="addAttribute" :disabled="isDisabled"> Add Attribute </v-btn>
        <v-btn text color="primary" @click="clearAndCancel"> Cancel </v-btn>
        <v-btn text color="primary" @click="submit"> Add Event </v-btn>
      </v-card-actions>
    </v-container>
  </v-card>
</template>

<script>
import dayjs from '@/plugins/dayjs'
import DatePicker from 'v-calendar/lib/components/date-picker.umd'
import ApiClient from '../../utils/RestApiClient'

export default {
  props: ['datetimeProp'],
  components: {
    DatePicker,
  },
  data() {
    return {
      message: null,
      timestampDesc: null,
      filterTab: null,
      showPicker: false,
      attributes: [],
      isDisabled: false,
      datetime: this.datetimeProp,
    }
  },
  watch: {
    datetimeProp: function (newValue) {
      this.datetime = newValue
    },
  },
  computed: {
    dateFromPicker: {
      set(val) {
        if (val !== null) this.datetime = dayjs.utc(val).millisecond(0).toISOString()
      },
      get() {
        return this.datetime
      },
    },
  },
  methods: {
    setAddAttributeBtn: function (i) {
      if (this.attributes[i].name === '' || this.attributes[i].value === '') {
        this.isDisabled = true
      } else {
        this.isDisabled = false
      }
    },
    addAttribute: function () {
      this.attributes.push({ name: '', value: '' })
      this.isDisabled = true
    },
    clearAndCancel: function () {
      this.datetime = null
      this.message = null
      this.timestampDesc = null
      this.attributes = []
      this.isDisabled = false
      this.$emit('cancel')
    },
    submit: function () {
      if (this.datetime === null || this.message === null || this.timestampDesc === null) {
        return
      }
      let sketchId = this.$store.state.sketch.id
      let config = {
        headers: {
          'Content-Type': 'application/json',
        },
      }
      let attributes = {}
      this.attributes.forEach((attribute) => {
        if (attribute.name === '' || attribute.value === '') return
        attributes[attribute.name] = attribute.value
      })
      ApiClient.createEvent(sketchId, this.datetime, this.message, this.timestampDesc, attributes, config)
        .then((response) => {
          this.clearAndCancel()
        })
        .catch((e) => {})
    },
  },
}
</script>

<style scoped lang="scss"></style>
