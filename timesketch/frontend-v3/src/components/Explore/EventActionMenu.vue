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
    <v-menu v-model="showMenu" :offset-x="true" :close-on-content-click="false">
      <template v-slot:activator="{ props }">
        <v-icon
          title="Event Action Menu"
          v-bind="props"
          class="ml-1"
          icon="mdi-dots-vertical"
          size="small"
        ></v-icon>
      </template>
      <v-list density="compact">
        <v-list-item @click="copyEventUrlToClipboard()">
          <template v-slot:prepend>
            <v-icon start icon="mdi-link-variant" size="small"></v-icon>
          </template>
          <v-list-item-title>Copy link to event</v-list-item-title>
        </v-list-item>
        <v-list-item link @click="copyEventAsJSON()">
          <template v-slot:prepend>
            <v-icon start icon="mdi-code-json" size="small"></v-icon>
          </template>
          <v-list-item-title>Copy event data as JSON</v-list-item-title>
        </v-list-item>
        <v-list-item link @click="showContextWindow()">
          <template v-slot:prepend>
            <v-icon start icon="mdi-magnify-plus-outline" size="small"></v-icon>
          </template>
          <v-list-item-title>Context search</v-list-item-title>
        </v-list-item>
      </v-list>
  </v-menu>
  </span>
</template>

<script>
import ApiClient from "@/utils/RestApiClient.js";
import EventBus from "@/event-bus.js";
import { useAppStore } from "@/stores/app.js";

export default {
  props: ["event"],
  data() {
    return {
      appStore: useAppStore(),
      showMenu: false,
      originalContext: false,
    };
  },
  computed: {
    sketch() {
      return this.appStore.sketch;
    },
    settings() {
      return this.appStore.settings;
    },
  },
  methods: {
    showContextWindow() {
      EventBus.$emit("showContextWindow", this.event);
      this.showMenu = false;
    },
    copyEventAsJSON() {
      ApiClient.getEvent(
        this.sketch.id,
        this.event._index,
        this.event._id,
        !!this.settings.showProcessingTimelineEvents
      )
        .then((response) => {
          let fullEvent = response.data.objects;
          let eventJSON = JSON.stringify(fullEvent, null, 3);
          navigator.clipboard.writeText(eventJSON);
          this.infoSnackBar("Event JSON copied to clipboard");
        })
        .catch((e) => {
          this.errorSnackBar("Failed to load JSON into the clipboard");
          console.error(e);
        });
      this.showMenu = false;
    },
    copyEventUrlToClipboard() {
      try {
        let eventUrl =
          window.location.origin +
          this.$route.path +
          '?q=_id:"' +
          this.event._id +
          '"';
        navigator.clipboard.writeText(eventUrl);
        this.infoSnackBar("Event URL copied to clipboard");
      } catch (error) {
        this.errorSnackBar("Failed to load Event URL into the clipboard");
        console.error(error);
      }
      this.showMenu = false;
    },

  },
};
</script>

<style scoped lang="scss"></style>
