<!--
Copyright 2025 Google Inc. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<template>
  <div
    class="position-absolute left-0 color-white pt-8 pb-6 rounded-lg dialog"
    v-click-outside="() => $emit('close-detail-popup')"
  >
    <v-btn
      variant="text"
      @click="$emit('close-detail-popup')"
      class="position-absolute top-0 right-0 pa-5"
    >
      <v-icon left small icon="mdi-close" color="#fff" />
    </v-btn>
    <v-table class="bg-none" density="compact" width="500px">
      <tbody>
        <tr v-if="eventId">
          <td>Event ID</td>
          <td>{{ eventId }}</td>
        </tr>
        <tr v-if="searchindexName">
          <td>Searchindex Name</td>
          <td>{{ searchindexName }}</td>
        </tr>
        <tr v-for="(value, key) in eventData" :key="key">
          <td>{{ key }}</td>
          <td>{{ value }}</td>
        </tr>
      </tbody>
    </v-table>
  </div>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  props: {
    eventData: Object,
    eventId: String,
    sketchId: Number,
    searchindexName: String
  },
  data() {
    return {
      store: useAppStore(),
      eventDetails: null,
      isLoading: true,
    };
  },
};
</script>

<style scoped>
.event-log .v-table__wrapper {
  overflow: visible;
}

.dialog {
  background-color: #424242;
  color: #fff;
  bottom: 100%;
  z-index: 3;
  width: 500px;
  max-height: 420px;
  overflow-y: auto;
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

td:nth-child(1) {
  width: 30%;
}

td:nth-child(2) {
  width: 70%;
  word-break: break-all;
}
</style>
