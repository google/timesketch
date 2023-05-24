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
        <v-icon v-bind="attrs" v-on="on" class="ml-1">mdi-dots-vertical</v-icon>
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
      </v-list>
    </v-menu>
  </span>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import EventBus from '../../main'

export default {
  props: ['event'],
  data() {
    return {
      showMenu: false,
      originalContext: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
  },
  methods: {
    showContextWindow() {
      EventBus.$emit('showContextWindow', this.event)
    },
    copyEventAsJSON() {
      ApiClient.getEvent(this.sketch.id, this.event._index, this.event._id)
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
        let eventUrl = window.location.origin + this.$route.path + '?q=_id:' + this.event._id
        navigator.clipboard.writeText(eventUrl)
        this.infoSnackBar('Event URL copied to clipboard')
      } catch (error) {
        this.errorSnackBar('Failed to load Event URL into the clipboard')
        console.error(error)
      }
    },
  },
}
</script>

<style scoped lang="scss"></style>
