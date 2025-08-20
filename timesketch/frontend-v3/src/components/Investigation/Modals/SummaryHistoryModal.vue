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
  <v-card class="modal overflow-hidden">
    <ModalLoader :isSubmitting="isSubmitting" />
    <div class="modal__content">
      <div class="modal__header pl-6 pr-1">
        <h3>
          <v-icon icon="mdi-creation" large class="mr-2" /> Summary History
        </h3>
        <v-btn
          variant="text"
          size="x-large"
          color="primary"
          @click="$emit('close-modal')"
        >
          <v-icon icon="mdi-close" large />
        </v-btn>
      </div>

      <div class="modal__content mb-5 px-16 py-6">
        <div class="summary" v-for="(summary, index) in summaries">
          <p class="summary__text mb-4">{{ summary.value }}</p>
          <div class="d-flex align-center ga-2">
            <div class="summary__time">
              <span>{{ index + 1 }} / {{ summaries.length }}</span>
              &#8226;
              <time>{{ formatDate(summary.timestamp) }}</time
              ><span v-if="summary.user"> by {{ summary.user }}</span>
            </div>
            <v-chip
              class="text-uppercase font-weight-bold"
              size="x-small"
              v-if="index === 0"
              >Currently Applied</v-chip
            >
          </div>
        </div>
      </div>
    </div>
  </v-card>
</template>

<script>
import { formatDate } from "@/utils/TimeDate";

export default {
  props: {
    summaries: Array,
  },
  data() {
    return {
      isSubmitting: false,
    };
  },
  methods: {
    formatDate,
  },
};
</script>

<style scoped>
.modal {
  background-color: #fff;
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #f3f4f5;
  height: 70px;
}

.modal__content {
  overflow: auto;
  -ms-overflow-style: none;
  scrollbar-width: none;
  height: 350px;
}

.summary {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #dadce0;
}

.summary__time {
  font-size: 14px;
  color: #5f6368;
}

.summary__text {
  white-space: pre-line;
}
</style>
