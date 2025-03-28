<!--
Copyright 2025 Google Inc. All rights reserved.

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
  <v-table :items="events" hide-default-footer="true" class="event-log">
    <thead>
      <tr>
        <th></th>
        <th v-for="header in headers">{{ header.text }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="fact in events" :key="fact.event_id">
        <ConclusionFact :fact="fact" :sketchId="store.sketch.id" />
      </tr>
    </tbody>
  </v-table>
  <v-dialog
    transition="dialog-bottom-transition"
    v-model="showEventLog"
    width="100%"
    max-width="100%"
    height="75vh"
    content-class="ma-0 bg-white"
    class="align-end"
    opacity="0.25"
    :scrollable="true"
  >
    <EventsLog :conclusionId="conclusionId" :existingEvents="existingEvents" />
  </v-dialog>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  inject: ["showEventLog"],
  props: {
    events: Array,
    conclusionId: String,
  },
  data() {
    return {
      store: useAppStore(),
    };
  },
  computed: {
    existingEvents() {
      if (!this.events || this.events.length < 1) {
        return [];
      }

      return this.events.map(({ _id }) => _id);
    },
    headers() {
      return [
        {
          text: "Description",
          width: "40",
          sortable: false,
        },
        {
          text: "Datetime (UTC) ",
          align: "start",
          width: "200",
          sortable: false,
        },
        {
          text: "File name",
          width: "40",
          sortable: false,
        },
      ];
    },
  },
};
</script>

<style>
.event-log .v-table__wrapper {
  overflow: visible;
}

.dialog {
  background-color: #424242;
  color: #fff;
  bottom: 100%;
  z-index: 3;
}

.dialog:after {
  display: block;
  content: "";
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-top: 10px solid #424242;
  position: absolute;
  bottom: -8px;
  left: 22px;
}

.bg-none {
  background: transparent;
  color: #fff;
}
</style>
