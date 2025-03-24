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
  <v-toolbar>
    <v-toolbar-title class="font-weight-bold">Add More Facts</v-toolbar-title>
    <v-text-field
      hide-details="auto"
      id="name"
      name="name"
      v-model="name"
      variant="outlined"
      density="compact"
      placeholder="Enter a query"
      :disabled="reportLocked"
      class="bg-white"
      @=""
    ></v-text-field>
    <div class="v-spacer"></div>
    <v-btn text @click="closeEventLog()">
      <v-icon icon="mdi-close" small />
    </v-btn>
  </v-toolbar>
  <div class="px-8 overflow-auto">
    <EventList
      v-if="targetObservableId"
      :targetObservableId="targetObservableId"
      :disableToolbar="true"
      :disableSettings="true"
      :showAddToFindings="true"
      :queryRequest="{
        queryString: '*',
        queryFilter: {
          from: 0,
          terminate_after: 10,
          size: 10,
          indices: ['_all'],
          order: 'asc',
          chips: [],
        },
      }"
    />
  </div>
</template>

<script>
import EventList from "@/components/Explore/EventList.vue";
import { useAppStore } from "@/stores/app";

export default {
  inject: ["closeEventLog"],
  props: {
    targetObservableId: String,
  },
  data() {
    return {
      store: useAppStore(),
    };
  },
  methods: {
    search: function (
      resetPagination = true,
      incognito = false,
      parent = false
    ) {
      let queryRequest = {};
      queryRequest["queryString"] = this.currentQueryString;
      queryRequest["queryFilter"] = this.currentQueryFilter;
      queryRequest["resetPagination"] = resetPagination;
      queryRequest["incognito"] = incognito;
      queryRequest["parent"] = parent;
      this.activeQueryRequest = queryRequest;
      this.showSearchDropdown = false;
    },
  },
};
</script>
