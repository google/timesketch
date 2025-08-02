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
  <td class="top-aligned-cell">
    <div class="d-flex align-items-start">
      <div class="position-relative">
        <EventDetailsPopup
        v-if="showLogDetail && fact && fact.document_id"
        :eventId="fact.document_id"
        :searchindexName="fact.searchindex_name"
        :eventData="eventData"
        :sketchId="sketchId"
        @close-detail-popup="toggleShowLogDetail()"
      />
        <v-btn variant="text" @click="toggleShowLogDetail()" :disabled="isLoading || !eventData || error" title="Show event details">
          <v-icon left small icon="mdi-file-code-outline" />
        </v-btn>
      </div>
      <v-btn
        variant="text"
        @click="triggerContextSearch"
        :disabled="isLoading || !eventData || error"
        title="Context search for this event"
      >
        <v-icon small icon="mdi-magnify-plus-outline" />
      </v-btn>
      <RemoveEventPopup :fact="fact" :conclusionId="conclusionId" />
    </div>
  </td>
  <template v-if="isLoading">
    <td class="top-aligned-cell"><v-skeleton-loader type="text" height="20"></v-skeleton-loader></td>
    <td class="top-aligned-cell"><v-skeleton-loader type="text" height="20"></v-skeleton-loader></td>
    <td class="top-aligned-cell"><v-skeleton-loader type="text" height="20"></v-skeleton-loader></td>
  </template>
  <template v-else-if="error">
    <td colspan="3" class="text-center font-italic red--text text--darken-2 top-aligned-cell">{{ error }}</td>
  </template>
  <template v-else-if="eventData">
    <td class="top-aligned-cell">{{ eventData.message || 'N/A' }}</td>
    <td class="top-aligned-cell">
      {{ eventData.datetime || 'N/A' }}
      <span v-if="eventData.timestamp_desc"> ({{ eventData.timestamp_desc }})</span>
    </td>
    <td class="font-weight-bold top-aligned-cell">{{ eventData.data_type || 'N/A' }}</td>
  </template>
  <template v-else>
    <td colspan="3" class="text-center font-italic top-aligned-cell">Event details not available.</td>
  </template>
</template>

<script>
import ApiClient from '@/utils/RestApiClient'
import EventBus from '@/event-bus'

export default {
  props: {
    fact: {
      type: Object,
      required: true,
    },
    conclusionId: {
      type: Number,
      required: true,
    },
    sketchId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      showLogDetail: false,
      eventData: null,
      isLoading: false,
      error: null,
    };
  },
  methods: {
    triggerContextSearch() {
      if (!this.eventData) return
      const fullEventObject = {
        _id: this.fact.document_id,
        _index: this.fact.searchindex_name,
        _source: this.eventData,
      }
      EventBus.$emit('showContextWindow', fullEventObject)
    },
    toggleShowLogDetail() {
      if (this.eventData && !this.error) {
        this.showLogDetail = !this.showLogDetail;
      }
    },
    async fetchEventDetails() {
      if (!this.fact || !this.fact.document_id || !this.fact.searchindex_name || !this.sketchId) {
        this.error = 'Required identifiers for fetching event details are missing.'
        this.eventData = null
        this.isLoading = false
        return;
      }
      this.isLoading = true;
      this.error = null;
      try {
        // Alternative Approach if this results in too many API calls in parallel: Use a OR connected search for _id.
        const response = await ApiClient.getEvent(this.sketchId, this.fact.searchindex_name, this.fact.document_id)
        this.eventData = response.data.objects ? response.data.objects : null
        if (!this.eventData) {
          this.error = 'Event not found or no data returned.'
        }
      } catch (e) {
        console.error('Error fetching event details:', e)
        this.error = 'Failed to load event details.'
        this.eventData = null
      } finally {
        this.isLoading = false;
      }
    },
  },
  mounted() {
    this.fetchEventDetails()
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

.top-aligned-cell {
  vertical-align: top;
}
</style>
