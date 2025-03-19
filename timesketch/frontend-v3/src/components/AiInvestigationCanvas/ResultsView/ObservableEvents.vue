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
            <div
              class="position-absolute left-0 color-white pt-8 pb-6 rounded-lg dialog"
              v-if="showLogDetail"
              style="width: 500px"
              v-click-outside="() => setShowLogDetail()"
            >
              <v-btn
                variant="text"
                @click="setShowLogDetail()"
                class="position-absolute top-0 right-0 pa-5"
              >
                <v-icon left small icon="mdi-close" color="#fff" />
              </v-btn>

              <v-table class="bg-none"  density="compact">
                <tbody>
                  <tr>
                    <td>data_type</td>
                    <td>syslog:line</td>
                  </tr>
                  <tr>
                    <td>display_name</td>
                    <td>EXT:/var/log/auth.log</td>
                  </tr>
                  <tr>
                    <td>hostname</td>
                    <td>vm-1</td>
                  </tr>
                  <tr>
                    <td>message</td>
                    <td>Accepted password for root from 43.133.102.2</td>
                  </tr>
                  <tr>
                    <td>reporter</td>
                    <td>sshd</td>
                  </tr>
                  <tr>
                    <td>source_long</td>
                    <td>Log File</td>
                  </tr>
                  <tr>
                    <td>timestamp</td>
                    <td>1696220923000000</td>
                  </tr>
                  <tr>
                    <td>timestamp_desc</td>
                    <td>Content Modification Time</td>
                  </tr>
                </tbody>
              </v-table>
            </div>
            <v-btn variant="text" @click="setShowLogDetail()">
              <v-icon left small icon="mdi-file-code-outline" />
            </v-btn>
          </div>
          <div class="position-relative">
            <div
              class="position-absolute left-0 color-white pa-6 rounded-lg dialog"
              v-if="showRemoveLog"
              style="width: 420px"
              v-click-outside="() => setShowRemoveLog()"
            >
              <h4 class="mb-3">Removing Log</h4>
              <p class="mb-5">
                Are you sure you want to remove this log? This action may not be
                reversible.
              </p>

              <div class="d-flex justify-end">
                <v-btn variant="text" size="small" @click="setShowRemoveLog()">
                  No, keep it
                </v-btn>
                <v-btn color="#fff" size="small" rounded @click="removeLog()">
                  Yes, remove It
                </v-btn>
              </div>
            </div>
            <v-btn variant="text" @click="setShowRemoveLog()">
              <v-icon small icon="mdi-close-circle-outline" />
            </v-btn>
          </div>
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
import RestApiClient from "@/utils/RestApiClient";

export default {
  props: {
    events: Array,
    details: Object,
  },
  data() {
    return {
      store: useAppStore(),
      showRemoveLog: false,
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
    setShowRemoveLog() {
      this.showRemoveLog = !this.showRemoveLog;
    },
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
