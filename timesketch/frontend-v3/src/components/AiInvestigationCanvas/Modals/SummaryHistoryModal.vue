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
  <div class="modal">
    <ModalLoader :isSubmitting="isSubmitting" />
    <div :class="modal__content">
      <div class="modal__header">
        <h3 class="mb-4">Summary History</h3>
        <v-btn
          variant="text"
          size="small"
          color="primary"
          @click="$emit('close-modal')"
        >
          <v-icon icon="mdi-close" class="mr-1" left small />
        </v-btn>
      </div>

      <div class="modal__content mb-5 px-16 py-6">
        <div class="summary" v-for="(summary, index) in summaries">
          <p class="mb-4">{{ summary.value }}</p>

          <div class="d-flex align-center ga-2">
            <div class="summary__time">
              <span class="mr-2">{{ index + 1 }} / {{ summaries.length }}</span>
              <time>{{ formatDate(summary.timestamp) }}</time>
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
  </div>
</template>

<script>
import { formatDate } from '@/utils/TimeDate';

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
    formatDate
  }
};
</script>

<style scoped>
.modal {
  background-color: #fff;
}

.modal__header {
  background-color: #f3f4f5;
}

.modal__content {
  display: grid;
  overflow: auto;
  -ms-overflow-style: none;
  scrollbar-width: none;
  overflow-y: auto;
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
</style>
