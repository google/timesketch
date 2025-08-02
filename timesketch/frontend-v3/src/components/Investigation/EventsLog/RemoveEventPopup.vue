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
  <div class="position-relative">
    <div
      class="position-absolute left-0 color-white pa-6 rounded-lg dialog"
      v-if="showRemoveLog"
      style="width: 420px"
      v-click-outside="() => toggleShowRemoveLog()"
    >
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
      <div v-else>
        <h4 class="mb-3">Unlink Event</h4>
        <p class="mb-5">
          Are you sure you want to unlink this event from this conclusion?
        </p>

        <div class="d-flex justify-end">
          <v-btn variant="text" size="small" @click="toggleShowRemoveLog()">
            No, keep it
          </v-btn>
          <v-btn
            color="#fff"
            size="small"
            @click="removeEventFromObservable()"
          >
            Yes, unlink It
          </v-btn>
        </div>
      </div>
    </div>
    <v-btn variant="text" @click="toggleShowRemoveLog()" title="Unlink Event from Conclusion">
      <v-icon small icon="mdi-link-variant-off" />
    </v-btn>
  </div>
</template>

<script>
import { useAppStore } from "@/stores/app";

export default {
  inject: ["updateObservables"],
  props: {
    fact: Object,
    conclusionId: Number
  },
  data() {
    return {
      store: useAppStore(),
      isLoading: false,
      showRemoveLog: false,
    };
  },
  methods: {
    async removeEventFromObservable() {
      // TODO: Unlink event from conclusion via the annotation function!
      try {
        this.isLoading = true;

        await this.updateObservables({
          conclusionId: this.conclusionId,
          events: [{"_id": this.fact.document_id, "_index": this.fact.searchindex_name}],
          remove: true,
        });

        this.toggleShowRemoveLog();

        this.store.setNotification({
          text: `Event ${this.eventId} removed from the observable.`,
          icon: "mdi-plus-circle-outline",
          type: "success",
        });
      } catch (error) {
        console.error(error);

        this.store.setNotification({
          text: "Unable to remove event from the observable.",
          icon: "mdi-alert-circle-outline",
          type: "error",
        });
      } finally {
        this.isLoading = false;
      }
    },
    toggleShowRemoveLog() {
      this.showRemoveLog = !this.showRemoveLog;
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
