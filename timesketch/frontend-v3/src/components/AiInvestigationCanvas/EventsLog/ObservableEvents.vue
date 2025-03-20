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
  <v-table :items="[details]" hide-default-footer="true" class="event-log">
    <thead>
      <tr>
        <th></th>
        <th v-for="item in headers">{{ item.text }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="item in [details]" :key="item.description">
        <td class="d-flex">
          <div class="position-relative">
            <EventDetailsPopup
              v-if="showLogDetail"
              :eventId="recordId"
              :sketchId="store.sketch.id"
              @close-detail-popup="setShowLogDetail()"
            />
            <v-btn variant="text" @click="setShowLogDetail()">
              <v-icon left small icon="mdi-file-code-outline" />
            </v-btn>
          </div>
          <RemoveEventPopup />
        </td>
        <td>{{ item.description }}</td>
        <td>{{ item.timestamp }}</td>
        <td class="font-weight-bold">{{ item.source_file }}</td>
      </tr>
    </tbody>
  </v-table>
</template>

<script>
import { useAppStore } from "@/stores/app";
import EventDetailsPopup from "./EventDetailsPopup.vue";
import RemoveEventPopup from "./RemoveEventPopup.vue";

export default {
  props: {
    events: Array,
    details: Object,
    recordId: String
  },
  data() {
    return {
      store: useAppStore(),
      showLogDetail: false,
    };
  },
  computed: {
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
  methods: {
    setShowLogDetail() {
      this.showLogDetail = !this.showLogDetail;
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
