<!--
Copyright 2025 Google LLC

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
  <v-container fluid>
    <!-- Search -->
    <v-card
      class="d-flex align-start mb-1 pa-1 mx-3 mt-3"
      elevation="0"
      style="border: 1px solid #e0e0e0"
    >
      <v-sheet>
        <ts-search-history-buttons
          @toggleSearchHistory="toggleSearchHistory()"
        ></ts-search-history-buttons>
      </v-sheet>
      <v-text-field
        v-model="currentQueryString"
        id="tsSearchInput"
        ref="searchInput"
        label="Search"
        placeholder="Search"
        single-line
        focused
        persistent-placeholder
        hide-details
        density="compact"
        variant="plain"
        class="mx-3 mt-1"
        append-inner-icon="mdi-magnify"
        @click:append-inner="search()"
        append-icon="mdi-help-circle-outline"
        @click:append="showSearchHelp = true"
        @keyup.enter="search()"
      >
        <v-menu
          v-model="showSearchDropdown"
          :offset="[19, 0]"
          activator="parent"
          :close-on-content-click="false"
          :close-on-click="true"
        >
          <ts-search-dropdown
            v-click-outside="onClickOutside"
            :selected-labels="selectedLabels"
            :query-string="currentQueryString"
            @set-active-view="searchView"
            @add-chip="addChip"
            @update-label-chips="updateLabelChips()"
            @close-on-click="showSearchDropdown = false"
            @node-click="jumpInHistory"
            @set-query-and-filter="setQueryAndFilter"
          >
          </ts-search-dropdown>
        </v-menu>
      </v-text-field>
    </v-card>

    <!-- Search Help Dialog -->
    <v-dialog v-model="showSearchHelp" max-width="1800" scrollable>
      <SearchHelpCard :flat="true" @close-dialog="showSearchHelp = false"></SearchHelpCard>
    </v-dialog>

    <!-- Search History -->
    <v-card
      class="mb-1 pa-1 mx-3 mt-3"
      elevation="0"
      style="border: 1px solid #e0e0e0"
      v-show="showSearchHistory"
      outlined
    >
      <v-toolbar density="compact" color="transparent">
        <v-toolbar-title>Search history</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-slider
          v-model="zoomLevel"
          density="compact"
          :thumb-label="false"
          append-icon="mdi-plus"
          prepend-icon="mdi-minus"
          min="0.1"
          max="1"
          step="0.1"
          class="mt-6"
        >
        </v-slider>

        <v-btn icon @click="showSearchHistory = false" class="ml-4">
          <v-icon title="Close search history">mdi-close</v-icon>
        </v-btn>
      </v-toolbar>

      <v-divider></v-divider>

      <div
        v-dragscroll
        class="pa-md-4 no-scrollbars"
        style="
          overflow: scroll;
          white-space: nowrap;
          max-height: 500px;
          min-height: 100px;
        "
      >
        <ts-search-history-tree
          @node-click="jumpInHistory"
          :show-history="showSearchHistory"
          v-bind:style="{ transform: 'scale(' + zoomLevel + ')' }"
          style="transform-origin: top left"
        ></ts-search-history-tree>
      </div>
    </v-card>

    <!-- Timeline picker -->
    <v-toolbar flat dense style="background-color: transparent" class="mt-n3">
        <v-btn small icon @click="showTimelines = !showTimelines">
        <v-icon v-if="showTimelines" title="Hide Timelines">mdi-chevron-up</v-icon>
        <v-icon v-else title="Show Timelines">mdi-chevron-down</v-icon>
        </v-btn>
        <span class="timeline-header">

        <!-- TODO <ts-upload-timeline-form-button btn-type="small"></ts-upload-timeline-form-button> -->

        <!-- TODO <v-dialog v-model="addManualEvent" width="600">
            <template v-slot:activator="{ on, attrs }">
            <v-btn small text rounded color="primary" v-bind="attrs" v-on="on">
                <v-icon left small> mdi-plus </v-icon>
                Add manual event
            </v-btn>
            </template>
            <ts-add-manual-event
            app
            @cancel="addManualEvent = false"
            :datetimeProp="datetimeManualEvent"
            ></ts-add-manual-event>
        </v-dialog> -->
        <v-btn size="small" variant="text" color="primary" @click.stop="enableAllTimelines()">
            <v-icon left small>mdi-eye</v-icon>
            <span>Select all</span>
        </v-btn>
        <v-btn size="small" variant="text" color="primary" @click.stop="disableAllTimelines()">
            <v-icon left small>mdi-eye-off</v-icon>
            <span>Unselect all</span>
        </v-btn>
        </span>
    </v-toolbar>
    <v-expand-transition>
        <div v-show="showTimelines">
        <ts-timeline-picker
            :current-query-filter="currentQueryFilter"
            :count-per-index="countPerIndex"
            :count-per-timeline="countPerTimeline"
        ></ts-timeline-picker>
        </div>
    </v-expand-transition>

    <!-- Time filter chips -->
    <div class="ml-3">
      <span v-for="(chip, index) in timeFilterChips" :key="index + chip.value">
        <v-menu offset-y content-class="menu-with-gap">
          <template v-slot:activator="{ props }">
            <v-chip variant="outlined" prepend-icon="mdi-clock-outline" v-bind="props">
              <span v-bind:style="[!chip.active ? { 'text-decoration': 'line-through', opacity: '50%' } : '']">
                <span>{{ chip.value.split(',')[0] }}</span>
                <span v-if="chip.type === 'datetime_range' && chip.value.split(',')[0] !== chip.value.split(',')[1]">
                  &rarr; {{ chip.value.split(',')[1] }}</span
                >
              </span>
            </v-chip>
          </template>
          <v-card>
            <v-list>
              <!-- Edit timefilter menu -->
              <v-menu
                offset-y
                :close-on-content-click="false"
                :close-on-click="true"
                nudge-top="70"
                content-class="menu-with-gap"
                allow-overflow
                style="overflow: visible"
              >
                <template v-slot:activator="{ props }">
                  <v-list-item v-bind="props">
                    <v-list-item-action>
                      <v-icon>mdi-square-edit-outline</v-icon>
                    </v-list-item-action>
                    <v-list-item-subtitle>Edit filter</v-list-item-subtitle>
                  </v-list-item>
                </template>
                <!-- <ts-filter-menu app :selected-chip="chip" @updateChip="updateChip($event, chip)"></ts-filter-menu> -->
              </v-menu>
              <v-list-item @click="copyFilterChip(chip)">
                <v-list-item-action>
                  <v-icon>mdi-content-copy</v-icon>
                </v-list-item-action>
                <v-list-item-subtitle>Copy filter</v-list-item-subtitle>
              </v-list-item>
              <v-list-item @click="toggleChip(chip)">
                <v-list-item-action>
                  <v-icon v-if="chip.active">mdi-eye-off</v-icon>
                  <v-icon v-else>mdi-eye</v-icon>
                </v-list-item-action>
                <v-list-item-subtitle
                  ><span v-if="chip.active">Temporarily disable</span
                  ><span v-else>Re-enable</span></v-list-item-subtitle
                >
              </v-list-item>
              <v-list-item @click="removeChip(chip)">
                <v-list-item-action>
                  <v-icon>mdi-delete</v-icon>
                </v-list-item-action>
                <v-list-item-subtitle>Remove filter</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card>
        </v-menu>
        <span v-if="index + 1 < timeFilterChips.length" class="mx-2"><small>OR</small></span>
      </span>
      <span>
        <v-menu
          v-model="timeFilterMenu"
          offset-y
          :close-on-content-click="false"
          :close-on-click="true"
          content-class="menu-with-gap"
          allow-overflow
          style="overflow: visible"
        >
          <template v-slot:activator="{ props }">
            <v-btn prepend-icon="mdi-clock-plus-outline" size="small" variant="text" rounded color="primary" v-bind="props" class="ml-2">
              Add timefilter
            </v-btn>
          </template>
          <ts-filter-menu @cancel="timeFilterMenu = false" @addChip="addChip"></ts-filter-menu>
        </v-menu>
      </span>
    </div>

    <!-- Eventlist -->
    <v-card flat class="mt-5 mx-3" color="transparent">
      <ts-event-list
        :query-request="activeQueryRequest"
        @countPerIndex="updateCountPerIndex($event)"
        @countPerTimeline="updateCountPerTimeline($event)"
      ></ts-event-list>
    </v-card>

  </v-container>
</template>

<script>
import ApiClient from "../utils/RestApiClient.js";
import EventBus from "../event-bus.js";
import { useAppStore } from "@/stores/app";

import { dragscroll } from "vue-dragscroll";

import TsSearchHistoryButtons from "@/components/Explore/SearchHistoryButtons.vue";
import TsSearchHistoryTree from "@/components/Explore/SearchHistoryTree.vue";
import TsSearchDropdown from "@/components/Explore/SearchDropdown.vue";
import TsEventList from "@/components/Explore/EventList.vue";
import TsTimelinePicker from "@/components/Explore/TimelinePicker.vue";
import TsFilterMenu from "@/components/Explore/FilterMenu.vue";

const defaultQueryFilter = () => {
  return {
    from: 0,
    terminate_after: 40,
    size: 40,
    indices: "_all",
    order: "asc",
    chips: [],
  };
};

export default {
  props: {
    sketchId: {
      type: String,
      required: true,
    },
  },
  directives: {
    dragscroll,
  },
  components: {
    TsSearchHistoryButtons,
    TsSearchHistoryTree,
    TsSearchDropdown,
    TsEventList,
    TsTimelinePicker,
    TsFilterMenu,
  },
  data() {
    return {
      appStore: useAppStore(),
      countPerIndex: {},
      countPerTimeline: {},
      currentItemsPerPage: 40,
      timeFilterMenu: false,
      selectedFields: [{ field: "message", type: "text" }],
      showRightSidePanel: false,
      addManualEvent: false,
      datetimeManualEvent: "",
      params: {},
      contextEvent: false,
      originalContext: false,
      showSearchDropdown: false,
      activeQueryRequest: {},
      currentQueryString: "",
      currentQueryFilter: defaultQueryFilter(),
      selectedLabels: [],
      showSearchHistory: false,
      showSearchHelp: false,
      zoomLevel: 0.7,
      zoomOrigin: {
        x: 0,
        y: 0,
      },
      // TODO: Refactor this into a configurable option
      quickTags: [
        {
          tag: "bad",
          color: "red",
          textColor: "white",
          label: "mdi-alert-circle-outline",
        },
        {
          tag: "suspicious",
          color: "orange",
          textColor: "white",
          label: "mdi-help-circle-outline",
        },
        {
          tag: "good",
          color: "green",
          textColor: "white",
          label: "mdi-check-circle-outline",
        },
      ],
      showTimelines: true,
    };
  },
  methods: {
    getQuickTag(tag) {
      return this.quickTags.find((el) => el.tag === tag);
    },
    updateCountPerIndex: function (count) {
      this.countPerIndex = count;
    },
    updateCountPerTimeline: function (count) {
      this.countPerTimeline = count;
    },
    toggleSearchHistory: function () {
      this.showSearchHistory = !this.showSearchHistory;
      if (this.showSearchHistory) {
        this.triggerScrollTo();
      }
    },
    setQueryAndFilter: function (searchEvent) {
      if (this.$route.name !== "Explore") {
        this.$router.push({
          name: "Explore",
          params: { sketchId: this.sketch.id },
        });
      }
      if (searchEvent.queryString) {
        this.currentQueryString = searchEvent.queryString;
      }

      // Preserve user defined filter instead of resetting, if it exist.
      if (!searchEvent.queryFilter) {
        searchEvent.queryFilter = this.currentQueryFilter;
      }
      this.currentQueryFilter = searchEvent.queryFilter;

      // Add any chips from the search event and make sure they are not in the
      // current filter already. E.g. don't add a star filter twice.
      if (searchEvent.chip) {
        const chipExist = this.currentQueryFilter.chips.find(
          (chip) => chip.value === searchEvent.chip.value
        );
        if (!chipExist) {
          this.currentQueryFilter.chips.push(searchEvent.chip);
        }
      }

      // Preserve user defined item count instead of resetting.
      this.currentQueryFilter.size = this.currentItemsPerPage;
      this.currentQueryFilter.terminate_after = this.currentItemsPerPage;

      // Run the search
      if (searchEvent.doSearch) {
        if (searchEvent.incognito) {
          this.search(true, true);
        } else {
          this.search();
        }
      }
    },

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
    searchView: function (viewId) {
      this.showSearchDropdown = false;

      if (this.$route.name !== "Explore") {
        this.$router.push({
          name: "Explore",
          params: { sketchId: this.sketch.id },
        });
      }

      if (viewId !== parseInt(viewId, 10) && typeof viewId !== "string") {
        viewId = viewId.id;
      }

      ApiClient.getView(this.sketchId, viewId)
        .then((response) => {
          let view = response.data.objects[0];
          this.currentQueryString = view.query_string;
          this.currentQueryFilter = JSON.parse(view.query_filter);
          if (
            !this.currentQueryFilter.fields ||
            !this.currentQueryFilter.fields.length
          ) {
            this.currentQueryFilter.fields = [
              { field: "message", type: "text" },
            ];
          }
          this.selectedFields = this.currentQueryFilter.fields;
          let chips = this.currentQueryFilter.chips;
          if (chips) {
            for (let i = 0; i < chips.length; i++) {
              if (chips[i].type === "label") {
                this.selectedLabels.push(chips[i].value);
              }
            }
          }
          this.contextEvent = false;
          this.search();
        })
        .catch((e) => {});
    },
    searchContext: function (event) {
      // TODO: Make this selectable in the UI
      const contextTime = 300;
      const numContextEvents = 500;

      this.contextEvent = event;
      if (!this.originalContext) {
        let currentQueryStringCopy = JSON.parse(
          JSON.stringify(this.currentQueryString)
        );
        let currentQueryFilterCopy = JSON.parse(
          JSON.stringify(this.currentQueryFilter)
        );
        this.originalContext = {
          queryString: currentQueryStringCopy,
          queryFilter: currentQueryFilterCopy,
        };
      }

      const dateTimeTemplate = "YYYY-MM-DDTHH:mm:ss";
      let startDateTimeMoment = this.$moment.utc(
        this.contextEvent._source.datetime
      );
      let newStartDate = startDateTimeMoment
        .clone()
        .subtract(contextTime, "s")
        .format(dateTimeTemplate);
      let newEndDate = startDateTimeMoment
        .clone()
        .add(contextTime, "s")
        .format(dateTimeTemplate);
      let startChip = {
        field: "",
        value:
          newStartDate + "," + startDateTimeMoment.format(dateTimeTemplate),
        type: "datetime_range",
        operator: "must",
        active: true,
      };
      let endChip = {
        field: "",
        value: startDateTimeMoment.format(dateTimeTemplate) + "," + newEndDate,
        type: "datetime_range",
        operator: "must",
        active: true,
      };
      // TODO: Use chips instead
      this.currentQueryString = "* OR " + "_id:" + this.contextEvent._id;

      this.currentQueryFilter.chips = [startChip, endChip];

      let isLegacy =
        this.meta.indices_metadata[this.contextEvent._index].is_legacy;
      if (isLegacy) {
        this.currentQueryFilter.indices = [this.contextEvent._index];
      } else {
        this.currentQueryFilter.indices = [
          this.contextEvent._source.__ts_timeline_id,
        ];
      }
      this.currentQueryFilter.size = numContextEvents;
      this.search();
    },
    removeContext: function () {
      this.contextEvent = false;
      this.currentQueryString = JSON.parse(
        JSON.stringify(this.originalContext.queryString)
      );
      this.currentQueryFilter = JSON.parse(
        JSON.stringify(this.originalContext.queryFilter)
      );
      this.search();
    },
    updateEnabledTimelines: function (timelineIds) {
      this.currentQueryFilter.indices = timelineIds;
      this.search();
    },
    toggleChip: function (chip) {
      // Treat undefined as active to support old chip formats.
      if (chip.active === undefined) {
        chip.active = true;
      }
      chip.active = !chip.active;
      this.search();
    },
    copyFilterChip(chip) {
      let textToCopy = "";
      // Different handling based on chip type
      if (chip.type.startsWith("datetime")) {
        // For datetime chips, just copy the value
        textToCopy = chip.value;
      } else {
        // For other chips, copy both field and value
        textToCopy =
          chip.operator === "must_not"
            ? `NOT ${chip.field ? `${chip.field}:` : ""}"${chip.value}"`
            : `${chip.field ? `${chip.field}:` : ""}"${chip.value}"`;
      }
      // Copy to clipboard
      navigator.clipboard
        .writeText(textToCopy)
        .then(() => {
          this.infoSnackBar("Copied to clipboard!");
        })
        .catch((e) => {
          this.errorSnackBar("Failed to copy to clipboard.");
          console.error(e);
        });
    },
    removeChip: function (chip, search = true) {
      let chipIndex = this.currentQueryFilter.chips.findIndex(
        (c) => c.value === chip.value
      );
      this.currentQueryFilter.chips.splice(chipIndex, 1);
      if (chip.type === "label") {
        this.selectedLabels = this.selectedLabels.filter(
          (label) => label !== chip.value
        );
      }
      if (search) {
        this.search();
      }
    },
    updateChip: function (newChip, oldChip) {
      // Replace the chip at the given index
      let chipIndex = this.currentQueryFilter.chips.findIndex(
        (c) => c.value === oldChip.value && c.type === oldChip.type
      );
      this.currentQueryFilter.chips.splice(chipIndex, 1, newChip);
      this.search();
    },
    addChip: function (chip) {
      // Legacy views don't support chips so we need to add an array in order
      // to upgrade the view to the new filter system.
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = [];
      }
      this.currentQueryFilter.chips.push(chip);
      this.search();
    },
    addChipFromHistogram: function (chip) {
      if (!this.currentQueryFilter.chips) {
        this.currentQueryFilter.chips = [];
      }
      this.currentQueryFilter.chips.forEach((chip) => {
        if (chip.type === "datetime_range") {
          this.removeChip(chip, false);
        }
      });
      this.addChip(chip);
    },
    toggleLabelChip: function (labelName) {
      let chip = {
        field: "",
        value: labelName,
        type: "label",
        operator: "must",
        active: true,
      };
      let chips = this.currentQueryFilter.chips;
      if (chips) {
        for (let i = 0; i < chips.length; i++) {
          if (chips[i].value === labelName) {
            this.removeChip(i);
            return;
          }
        }
      }
      this.addChip(chip);
    },
    updateLabelChips: function () {
      // Remove all current label chips
      this.currentQueryFilter.chips = this.currentQueryFilter.chips.filter(
        (chip) => chip.type !== "label"
      );
      this.selectedLabels.forEach((label) => {
        let chip = {
          field: "",
          value: label,
          type: "label",
          operator: "must",
          active: true,
        };
        this.addChip(chip);
        this.showSearchDropdown = false;
      });
    },
    updateLabelList: function (label) {
      if (this.meta.filter_labels.indexOf(label) === -1) {
        this.meta.filter_labels.push(label);
      }
    },
    jumpInHistory: function (node) {
      this.currentQueryString = node.query_string;
      this.currentQueryFilter = JSON.parse(node.query_filter);
      if (
        !this.currentQueryFilter.fields ||
        !this.currentQueryFilter.fields.length
      ) {
        this.currentQueryFilter.fields = [{ field: "message", type: "text" }];
      }
      this.selectedFields = this.currentQueryFilter.fields;
      if (
        this.currentQueryFilter.indices[0] === "_all" ||
        this.currentQueryFilter.indices === "_all"
      ) {
        let allIndices = [];
        this.sketch.active_timelines.forEach((timeline) => {
          let isLegacy =
            this.meta.indices_metadata[timeline.searchindex.index_name]
              .is_legacy;
          if (isLegacy) {
            allIndices.push(timeline.searchindex.index_name);
          } else {
            allIndices.push(timeline.id);
          }
        });
        this.currentQueryFilter.indices = allIndices;
      }
      let chips = this.currentQueryFilter.chips;
      if (chips) {
        for (let i = 0; i < chips.length; i++) {
          if (chips[i].type === "label") {
            this.selectedLabels.push(chips[i].value);
          }
        }
      }
      this.contextEvent = false;
      this.search(true, true, node.id);
    },
    triggerScrollTo: function () {
      EventBus.$emit("triggerScrollTo");
    },
    zoomWithMouse: function (event) {
      // Add @wheel="zoomWithMouse" on element to activate.
      this.zoomOrigin.x = event.pageX;
      this.zoomOrigin.y = event.pageY;
      if (event.deltaY < 0) {
        this.zoomLevel += 0.07;
      } else if (event.deltaY > 0) {
        this.zoomLevel -= 0.07;
      }
    },
    closeSearchDropdown: function (targetElement) {
      // Prevent dropdown to close when the search input field is clicked.
      if (
        targetElement !== this.$refs.searchInput &&
        targetElement.getAttribute("data-explore-element") === null
      ) {
        this.showSearchDropdown = false;
      }
    },
    onClickOutside: function (e) {
      if (e.target.id !== "tsSearchInput") {
        this.showSearchDropdown = false;
      }
    },
    enableAllTimelines() {
      this.appStore.updateEnabledTimelines(
        this.activeTimelines.map((tl) => tl.id)
      );
    },
    disableAllTimelines() {
      this.appStore.updateEnabledTimelines([]);
    },
  },
  computed: {
    sketch() {
      return this.appStore.sketch;
    },
    meta() {
      return this.appStore.meta;
    },
    enabledTimelines() {
      return this.appStore.enabledTimelines;
    },
    filterChips: function () {
      return this.currentQueryFilter.chips.filter(
        (chip) => chip.type === "label" || chip.type === "term"
      );
    },
    timeFilterChips: function () {
      return this.currentQueryFilter.chips.filter((chip) =>
        chip.type.startsWith("datetime")
      );
    },
    filteredLabels() {
      return this.appStore.meta.filter_labels.filter(
        (label) => !label.label.startsWith("__")
      );
    },
    currentSearchNode() {
      return this.appStore.currentSearchNode;
    },
    activeContext() {
      return this.appStore.activeContext;
    },
    activeTimelines() {
      // Sort alphabetically based on timeline name.
      let timelines = [...this.sketch.active_timelines];
      return timelines.sort(function (a, b) {
        return a.name.localeCompare(b.name);
      });
    },
  },
  mounted() {
    this.$refs.searchInput.focus();
    EventBus.$on("setQueryAndFilter", this.setQueryAndFilter);
    EventBus.$on("setActiveView", this.searchView);
  },
  beforeDestroy() {
    EventBus.$off("setQueryAndFilter");
    EventBus.$off("setActiveView");
  },
  created: function () {
    let doSearch = false;

    this.params = {
      viewId: this.$route.query.view,
      indexName: this.$route.query.timeline,
      resultLimit: this.$route.query.limit,
      queryString: this.$route.query.q,
    };

    if (this.params.viewId) {
      this.searchView(this.params.viewId);
      return;
    }

    if (this.params.queryString) {
      this.currentQueryString = this.params.queryString;
      doSearch = true;
    }

    if (this.params.indexName) {
      if (!this.params.queryString) {
        this.currentQueryString = "*";
      }

      let timeline = this.sketch.active_timelines.find((timeline) => {
        return timeline.id === parseInt(this.params.indexName, 10);
      });

      let isLegacy =
        this.meta.indices_metadata[timeline.searchindex.index_name].is_legacy;
      if (isLegacy) {
        this.currentQueryFilter.indices = [timeline.searchindex.index_name];
      } else {
        this.currentQueryFilter.indices = [timeline.id];
      }
      doSearch = true;
    }

    if (!this.currentQueryString) {
      this.currentQueryFilter.indices = ["_all"];
    }

    if (doSearch) {
      if (!this.currentQueryFilter.indices.length) {
        this.currentQueryFilter.indices = ["_all"];
      }
      this.search();
    }
  },
  watch: {
    enabledTimelines: function () {
      this.updateEnabledTimelines(this.enabledTimelines);
    },
  },
};
</script>

<style lang="scss">
.chip-disabled {
  text-decoration: line-through;
  opacity: 0.5;
}

.chip-operator-label {
  margin-right: 7px;
  font-size: 0.7em;
  cursor: default;
}

.no-scrollbars::-webkit-scrollbar {
  display: none;
}

.no-scrollbars {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.filter-chip-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}

.expanded .timeline-header {
  .v-icon.open-indicator {
    display: inline;
  }
  .v-icon.closed-indicator {
    display: none;
  }
}
.timeline-header {
  display: flex;
  align-items: center;

  .v-icon.open-indicator {
    display: none;
  }
}
</style>
