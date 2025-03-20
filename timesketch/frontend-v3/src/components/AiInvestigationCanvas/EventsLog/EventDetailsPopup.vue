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
    <div
      v-if="isLoading"
      class="d-flex justify-center align-center pa-6 fill-height"
    >
      <v-progress-circular
        :size="80"
        :width="4"
        color="#fff"
        indeterminate
      ></v-progress-circular>
    </div>
    <v-table v-else class="bg-none" density="compact" width="500px">
      <tbody v-if="fullEventFiltered">
        <tr v-for="([key, value], index) in fullEventFiltered">
          <td>{{ key }}</td>
          <td>{{ value }}</td>
        </tr>
      </tbody>
    </v-table>
  </div>
</template>

<script>
import { useAppStore } from "@/stores/app";
import RestApiClient from "@/utils/RestApiClient";

export default {
  props: {
    eventId: String,
    sketchId: String,
  },
  data() {
    return {
      store: useAppStore(),
      eventDetails: null,
      isLoading: true,
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
    fullEventFiltered() {
      if (!this.eventDetails) {
        return [];
      }

      console.log(Object.entries(this.eventDetails));

      return Object.entries(this.eventDetails);
    },
  },
  async mounted() {
    await this.fetchEventDetail();
  },
  methods: {
    async fetchEventDetail() {
      this.isLoading = true;
      try {
        const queryResponse = await RestApiClient.search(this.sketchId, {
          query: `event_id: ${this.eventId}`,
        });

        if (!queryResponse.data.objects?.[0]) {
          throw error;
        }

        this.eventDetails = queryResponse.data.objects?.[0]?._source;
      } catch (error) {
        this.store.setNotification({
          text: "Unable to retrieve detailed information",
          icon: "mdi-alert-circle-outline",
          type: "error",
        });

        this.$emit("close-detail-popup");
      } finally {
        this.isLoading = false;
      }
    },
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
  height: 420px;
  overflow: hidden;
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
