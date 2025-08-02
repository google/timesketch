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
  <div :class="['filterbar__wrapper', {'filterbar__wrapper--expanded': expanded}]">
    <div class="filterbar__header">
      <h4 class="filterbar__heading" v-if="questions.length">
        <span v-if="displayTotal !== filteredAndSortedQuestions.length" class="font-weight-bold">{{ filteredAndSortedQuestions.length }} / </span>
        <span :class="displayTotal === filteredAndSortedQuestions.length ? 'font-weight-bold' : ''">{{ displayTotal }}</span>
        <span class="font-weight-regular"> question{{ displayTotal > 1 && 's' }}</span>
        <span class="filterbar__progress font-weight-regular" v-if="expanded && questionsTotal">
          {{ completedQuestionsTotal }} / {{ questionsTotal }} questions answered
        </span>
      </h4>

      <v-btn
        class="filterbar__clear-btn"
        color="var(--theme-ai-color-blue-600)"
        variant="text"
        @click="clearAllFilters"
        density="compact"
        :disabled="!hasActiveFilters"
      >
        Clear All
      </v-btn>
    </div>

    <div class="filterbar">
      <div class="filterbar__item">
        <v-select
          :class="['filterbar__select', selectedStatuses.length && 'filterbar__select--active']"
          color="var(--theme-ai-color-blue-500)"
          :items="statusFilterItems"
          v-model="selectedStatuses"
          multiple
          density="compact"
          variant="outlined"
          hide-details
          placeholder="Status"
        >
          <template #selection="{ index }">
            <span v-if="index === 0">
              Status<span v-if="selectedStatuses.length"> ({{ selectedStatuses.length }})</span>
            </span>
          </template>
        </v-select>
        <p class="filterbar__item-label">
          Status<span v-if="selectedStatuses.length"> ({{ selectedStatuses.length }})</span>
        </p>
      </div>

      <div class="filterbar__item">
        <v-select
          :class="['filterbar__select', selectedPriorities.length && 'filterbar__select--active']"
          color="var(--theme-ai-color-blue-500)"
          :items="['High Priority', 'Medium Priority', 'Low Priority']"
          v-model="selectedPriorities"
          multiple
          density="compact"
          variant="outlined"
          hide-details
          placeholder="Priority"
        >
          <template #selection="{ index }">
            <span v-if="index === 0">
              Priority<span v-if="selectedPriorities.length"> ({{ selectedPriorities.length }})</span>
            </span>
          </template>
        </v-select>
        <p class="filterbar__item-label">
          Priority<span v-if="selectedPriorities.length"> ({{ selectedPriorities.length }})</span>
        </p>
      </div>

      <div class="filterbar__item">
        <v-select
          :class="['filterbar__select', selectedCreatedBy.length && 'filterbar__select--active']"
          color="var(--theme-ai-color-blue-500)"
          :items="createdByOptions"
          v-model="selectedCreatedBy"
          multiple
          density="compact"
          variant="outlined"
          hide-details
          placeholder="Created By"
        >
          <template #selection="{ index }">
            <span v-if="index === 0">
              Created By<span v-if="selectedCreatedBy.length"> ({{ selectedCreatedBy.length }})</span>
            </span>
          </template>
        </v-select>
        <p class="filterbar__item-label">
          Created By<span v-if="selectedCreatedBy.length"> ({{ selectedCreatedBy.length }})</span>
        </p>
      </div>

      <div class="filterbar__item filterbar__item--sort">
        <v-select
          :class="['filterbar__select', selectedSort && 'filterbar__select--active']"
          color="var(--theme-ai-color-blue-500)"
          :items="sortOptions"
          v-model="selectedSort"
          density="compact"
          variant="outlined"
          hide-details
          placeholder="Sort"
        >
          <template #selection="{ index }">
            <v-icon icon="mdi-swap-vertical" class="filterbar__select-icon" start></v-icon>
            <span v-if="index === 0">Sort</span>
          </template>
        </v-select>
        <p class="filterbar__item-label">Sort</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    questionsTotal: Number,
    completedQuestionsTotal: Number,
    questions: Array,
    expanded: {
      type: Boolean,
      default: false
    },
    view: {
      type: String,
      default: 'sidebar',
    },
  },
  data() {
    return {
      selectedStatuses: [],
      selectedPriorities: [],
      selectedCreatedBy: [],
      selectedSort: '',
    }
  },
  computed: {
    statusFilterItems() {
      const allStatuses = ['New', 'Pending Review', 'Verified', 'Rejected'];
      if (this.view === 'report') {
        return allStatuses.filter(status => status !== 'Rejected');
      }
      return allStatuses;
    },
    displayTotal() {
      if (this.view === 'report') {
        return this.questions.filter(q => q.status?.status !== 'rejected').length;
      }
      return this.questions.length;
    },
    createdByOptions() {
      if (!this.questions) return []
      const names = this.questions.map((q) => q.user?.name)
      const usernames = Array.from(new Set(names.filter(Boolean)))
      return ['AI Generated', 'User Generated', ...usernames]
    },
    sortOptions() {
      return ['Date Created Earliest', 'Date Created Latest', 'Status', 'Priority']
    },
    filteredAndSortedQuestions() {
      if (!this.questions?.length) return []

      function getPriority(q) {
        const label = q.labels?.find((l) => l.name && l.name.startsWith('__ts_priority_'))
        return label ? label.name.replace('__ts_priority_', '').toLowerCase() : 'none'
      }

      function getStatus(q) {
        return q.status?.status?.toLowerCase() || ''
      }

      let filtered = this.questions

      // If in report view, always exclude rejected questions from the filterable list first.
      if (this.view === 'report') {
        filtered = filtered.filter(q => q.status?.status !== 'rejected');
      }

      // Filter by Status
      if (this.selectedStatuses.length) {
        const normalizedSelected = this.selectedStatuses.map((s) => s.toLowerCase())
        filtered = filtered.filter((q) => {
          const statusValue = q.status?.status?.toLowerCase().replace(/-/g, ' ') || 'none'
          return normalizedSelected.includes(statusValue)
        })
      }

      // Filter by Priority
      if (this.selectedPriorities.length) {
        const normalizedPriorities = this.selectedPriorities.map((p) => p.toLowerCase())
        filtered = filtered.filter((q) => {
          const priorityValue = getPriority(q)
          return normalizedPriorities.some((sel) => sel.includes(priorityValue))
        })
      }

      // Filter by Created By
      if (this.selectedCreatedBy.length) {
        filtered = filtered.filter((q) => {
          const creator = q.user && q.user.name ? q.user.name : 'AI Generated';
          const isUserCreated = !!(q.user && q.user.name);

          // Return true if any of the selected criteria match the question
          return this.selectedCreatedBy.some(selection => {
            if (selection === 'User Generated') {
              return isUserCreated;
            }
            return creator === selection;
          });
        });
      }

      // Sorting logic
      let sorted = [...filtered]
      switch (this.selectedSort) {
        case 'Date Created Earliest':
          sorted.sort((a, b) => new Date(a.created_at || a.createdAt) - new Date(b.created_at || b.createdAt))
          break
        case 'Date Created Latest':
          sorted.sort((a, b) => new Date(b.created_at || b.createdAt) - new Date(a.created_at || a.createdAt))
          break
        case 'Status':
          const statusOrder = ['verified', 'pending-review', 'new', 'rejected']
          sorted.sort((a, b) => {
            const aStatus = getStatus(a)
            const bStatus = getStatus(b)
            return statusOrder.indexOf(aStatus) - statusOrder.indexOf(bStatus)
          })
          break
        case 'Priority':
          const priorityOrder = ['high', 'medium', 'low', 'none']
          sorted.sort((a, b) => {
            const aPriority = getPriority(a)
            const bPriority = getPriority(b)
            const aIdx =
              priorityOrder.indexOf(aPriority) === -1 ? priorityOrder.length : priorityOrder.indexOf(aPriority)
            const bIdx =
              priorityOrder.indexOf(bPriority) === -1 ? priorityOrder.length : priorityOrder.indexOf(bPriority)
            return aIdx - bIdx
          })
          break
        default:
          sorted.sort((a, b) => a.id - b.id)
      }
      return sorted
    },
    hasActiveFilters() {
      return (
        this.selectedStatuses.length > 0 ||
        this.selectedPriorities.length > 0 ||
        this.selectedCreatedBy.length > 0 ||
        this.selectedSort
      )
    },
  },
  methods: {
    clearAllFilters() {
      this.selectedSort = ''
      this.selectedStatuses = []
      this.selectedPriorities = []
      this.selectedCreatedBy = []
    },
  },
  watch: {
    filteredAndSortedQuestions: {
      handler(newVal) {
        this.$emit('filters-changed', newVal)
      },
      immediate: true
    },
  },
}
</script>

<style scoped>
.filterbar__heading {
  font-size: 14px;
  color: var(--theme-ai-color-black);
  font-weight: 700;
  flex: 1 1 auto;
  padding: 1px 0 0 3px;

  span {
    color: var(--theme-ai-color-gray-600);
    font-weight: 400;
  }
}

.filterbar__wrapper {
  padding: 0 0 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 14px 16px;
}

.filterbar__wrapper--expanded {
  flex-wrap: nowrap;
}

.filterbar__header {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
  align-items: center;
  flex: 1 1 100%;
}

.filterbar {
  padding: 0;
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  align-items: center;
  justify-content: flex-start;
  align-items: baseline;
  flex: 1 1 100%;
}

.filterbar__wrapper--expanded .filterbar {
  flex: 0 0 auto;
}

.filterbar__label {
  font-size: 14px;
  font-weight: 500;
  color: var(--theme-ai-color-gray-700);
}

.filterbar__item {
  position: relative;
  flex: 0 0 auto;
}

.filterbar__item--sort {
  margin-left: auto;
  min-width: 95px;
}

.filterbar__item:not(.filterbar__item--sort) {
  &:deep(.v-field__append-inner),
  &:deep(.v-select__menu-icon) {
    display: none !important;
  }
}

.filterbar__item-label {
  opacity: 0;
  pointer-events: none;
  font-size: 14px;
  font-weight: 500;
  padding: 0 17px;
  height: 34px;
  display: block;
  letter-spacing: 0.1px;
}

.filterbar__select {
  min-width: 73px;
  width: 100% !important;
  font-size: 14px;
  font-weight: 500;
  position: absolute;
  inset: 0 0 auto 0;

  &:deep(input::placeholder) {
    opacity: 1 !important;
    color: var(--theme-ai-color-gray-700) !important;
  }

  &:deep(.v-field) {
    padding: 0 !important;
    font-size: 14px;
  }

  &:deep(.v-field__append-inner) {
    margin-right: 4px;
  }

  &:deep(.v-field__outline) {
    border-radius: 8px;
    color: var(--theme-ai-color-gray-200) !important;
    --v-field-border-opacity: 1;
  }

  &:deep(.v-field__input) {
    --v-input-control-height: 34px;
    --v-field-padding-start: 16px;
    --v-field-padding-end: 16px;
    --v-field-input-padding-top: 0px;
    --v-field-input-padding-bottom: 0px;
    justify-content: center;
    white-space: nowrap;

    input {
      align-self: center;
      text-align: center;
      left: 0;
    }
  }

  &:deep(.v-select__selection) {
    margin-inline-end: 0 !important;
    color: var(--theme-ai-color-gray-700) !important;
  }
}

.filterbar__select-icon {
  width: 18px;
  height: 18px;
  margin: 0 6px 0 -8px;
}

.filterbar__select--active {
  background-color: var(--theme-ai-color-blue-50);
  color: var(--theme-ai-color-blue-700);
}

.filterbar__clear-btn {
  font-size: 12px;
  font-weight: 400;
  text-decoration: underline;
  flex: 0 0 auto;
  padding: 0 3px !important;
  text-transform: none;
  letter-spacing: 0;
  min-width: 0;
  color: var(--theme-ai-color-blue-600) !important;
  height: auto;
}

.filterbar__progress {
  position: relative;
  margin-left: 17px;
  padding-left: 17px;

  &::after {
    content: '';
    position: absolute;
    top: -4px;
    left: 0;
    width: 1px;
    height: 26px;
    background-color: var(--theme-ai-color-gray-100);
  }
}
</style>
