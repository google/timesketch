<!--
Copyright 2023 Google Inc. All rights reserved.

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
  <span>
    <v-menu v-model="showMenu" offset-y transition="slide-y-transition">
      <template v-slot:activator="{ on, attrs }">
        <v-icon title="Event Action Menu" v-bind="attrs" v-on="on" class="ml-1">mdi-dots-vertical</v-icon>
      </template>
      <v-list dense class="mx-auto">
        <v-list-item style="cursor: pointer" @click="copyEventUrlToClipboard()">
          <v-list-item-icon>
            <v-icon small>mdi-link-variant</v-icon>
          </v-list-item-icon>
          <v-list-item-title>Copy link to event</v-list-item-title>
        </v-list-item>
        <v-list-item style="cursor: pointer" @click="copyEventAsJSON()">
          <v-list-item-icon>
            <v-icon small>mdi-code-json</v-icon>
          </v-list-item-icon>
          <v-list-item-title>Copy event data as JSON</v-list-item-title>
        </v-list-item>
        <v-list-item style="cursor: pointer" @click="showContextWindow()">
          <v-list-item-icon>
            <v-icon small>mdi-magnify-plus-outline</v-icon>
          </v-list-item-icon>
          <v-list-item-title>Context search</v-list-item-title>
        </v-list-item>
        <v-list-item style="cursor: pointer" @click="focusOnTimeline()">
          <v-list-item-icon>
            <v-icon small>mdi-eye</v-icon>
          </v-list-item-icon>
          <v-list-item-title>Unselect other timelines</v-list-item-title>
        </v-list-item>
        <v-list-item style="cursor: pointer" @click="filterOutTimeline()">
          <v-list-item-icon>
            <v-icon small>mdi-eye-off</v-icon>
          </v-list-item-icon>
          <v-list-item-title>Unselect this timeline</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </span>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import EventBus from '../../event-bus.js'
import EventMixin from '../../mixins/EventMixin'

export default {
  props: ['event'],
  data() {
    return {
      showMenu: false,
      originalContext: false,
    }
  },
  mixins: [EventMixin],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    settings() {
      return this.$store.state.settings
    },
  },
  methods: {
    showContextWindow() {
      EventBus.$emit('showContextWindow', this.event)
    },
    copyEventAsJSON() {
      ApiClient.getEvent(this.sketch.id, this.event._index, this.event._id, !!this.settings.showProcessingTimelineEvents)
        .then((response) => {
          let fullEvent = response.data.objects
          let eventJSON = JSON.stringify(fullEvent, null, 3)
          navigator.clipboard.writeText(eventJSON)
          this.infoSnackBar('Event JSON copied to clipboard')
        })
        .catch((e) => {
          this.errorSnackBar('Failed to load JSON into the clipboard')
          console.error(e)
        })
    },
    copyEventUrlToClipboard() {
      try {
        let eventUrl = window.location.origin + this.$route.path + '?q=_id:"' + this.event._id + '"'
        navigator.clipboard.writeText(eventUrl)
        this.infoSnackBar('Event URL copied to clipboard')
      } catch (error) {
        this.errorSnackBar('Failed to load Event URL into the clipboard')
        console.error(error)
      }
    },
    focusOnTimeline() {
      const timeline = this.getTimeline(this.event)
      if (!timeline) return
      this.$store.dispatch('updateEnabledTimelines', [timeline.id])
    },
    filterOutTimeline() {
      const timeline = this.getTimeline(this.event)
      if (!timeline) return
      const currentEnabled = this.$store.state.enabledTimelines || []
      const newEnabled = currentEnabled.filter((id) => id !== timeline.id)
      this.$store.dispatch('updateEnabledTimelines', newEnabled)
    },
  },
}
</script>

<style scoped lang="scss"></style>
