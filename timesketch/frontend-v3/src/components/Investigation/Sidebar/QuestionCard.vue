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
  <v-list-item
    base-color="var(--theme-ai-color-blue-200)"
    :class="['question-card', isActive && 'question-card--active']"
    :active="isActive"
    @click="setActiveQuestion()"
  >
    <div class="question-card__content">
      <div class="d-flex ga-6 align-center">
        <v-avatar v-if="user.name" size="24" class="question-card__avatar">
          <span>{{ $filters.initialLetter(user.name) }}</span>
        </v-avatar>
        <CreationIcon v-else class="question-card__icon" :width="24" :height="24" />
        <p :class="isRejected ? 'is-rejected-text' : 'font-weight-medium black--text'" style="text-wrap: pretty">{{ name }}</p>
      </div>
      <div class="d-flex ga-2 align-center flex-1-1-100" v-if="hasChips">
        <v-chip v-if="priority" :class="['chip', priorityColor]" small label :title="`Priority: ${priority}`">
          {{ priority }} Priority
        </v-chip>
        <v-chip v-if="isApproved" small label title="Verified" :class="['chip', 'chip--verified']">
          <v-icon icon="mdi-check-circle-outline" start></v-icon>
          Verified
        </v-chip>
        <v-chip v-if="isRejected" small label title="Rejected" :class="['chip', 'chip--rejected']">
          <v-icon icon="mdi-close" start></v-icon>
          Rejected
        </v-chip>
        <v-chip v-if="isPending" small label title="Pending Review" :class="['chip', 'chip--pending']">
          <v-icon icon="mdi-magnify" start></v-icon>
          Pending Review
        </v-chip>
        <v-chip v-if="isNew" small label title="New" :class="['chip', 'chip--new']">
          <v-icon icon="mdi-star-outline" start></v-icon>
          New
        </v-chip>
      </div>
    </div>
  </v-list-item>
</template>

<script>
import CreationIcon from '@/components/Icons/CreationIcon'
import { useAppStore } from '@/stores/app'
import { getPriorityFromLabels } from '@/components/Investigation/_utils/QuestionPriority.js'

export default {
  components: {
    CreationIcon,
  },
  props: {
    value: Object,
    name: String,
    type: String,
    conclusion: String,
    conclusionSummary: String,
    conclusions: Array,
    updatedAt: String,
    id: Number,
    user: Object,
    index: Number,
    labels: Array,
    status: Object,
  },
  data() {
    return {
      store: useAppStore(),
    }
  },
  methods: {
    setActiveQuestion() {
      this.store.setActiveQuestion(this.value)
    },
  },
  computed: {
    hasChips() {
      return this.priority || this.isApproved || this.isRejected || this.isNew || this.isPending
    },
    isActive() {
      return this.store.activeContext.question?.id ? this.id === this.store.activeContext.question?.id : false
    },
    isRejected() {
      return this.status?.status === 'rejected'
    },
    isPending() {
      return this.status?.status === 'pending-review'
    },
    isNew() {
      return this.status?.status === 'new'
    },
    isApproved() {
      return this.status?.status === 'verified'
    },
    priority() {
      return getPriorityFromLabels(this.labels)
    },
    priorityColor() {
      if (!this.priority) return 'chip--none'
      switch (this.priority.toLowerCase()) {
        case 'high':
          return 'chip--high'
        case 'medium':
          return 'chip--medium'
        case 'low':
          return 'chip--low'
        default:
          return 'chip--none'
      }
    },
  },
}
</script>

<style scoped>
.question-card {
  background-color: var(--theme-ai-color-white);
  padding: 0 !important;
  border-bottom: 1px solid var(--theme-ai-color-gray-300);
  position: relative;
  --v-activated-opacity: 0;

  p {
    line-height: 1.4;
    color: var(--theme-ai-color-black);
  }

  .is-rejected-text {
    font-weight: light;
    color: var(--theme-ai-color-gray-600);
  }

  &::after {
    content: '';
    display: block;
    width: 6px;
    position: absolute;
    inset: 0 0 0 auto;
    pointer-events: none;
    border: none;
    border-radius: 0;
    opacity: 1;
  }

  &.question-card--active {
    &::after {
      background-color: var(--theme-ai-color-blue-500);
    }
  }
}

.question-card__content {
  padding: 24px 20px;
  display: grid;
  grid-template-columns: 1fr;
  align-content: space-between;
  gap: 16px;
}

.question-card__avatar {
  background-color: #eaddff;

  span {
    font-size: 12px;
    font-weight: 500;
    color: var(--theme-ai-color-blue-800);
  }
}

.question-card__icon {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
}

.chip {
  --v-chip-height: 20px;
  padding: 0 4px;
  font-weight: 700;
  font-size: 10px;
  line-height: 1;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;

  &:deep(.v-chip__underlay) {
    display: none !important;
  }

  &:has(.v-icon--start) {
    padding-left: 11px;

    &:deep(.v-icon--start) {
      margin-inline-end: 4px;
    }
  }

  &.chip--high {
    background-color: var(--theme-ai-color-red-100);
    color: var(--theme-ai-color-red-900);
  }

  &.chip--medium {
    background-color: #f9e3cc;
    color: #703a00;
  }

  &.chip--low {
    background-color: var(--theme-ai-color-yellow-100);
    color: #574100;
  }

  &.chip--none {
    background-color: var(--theme-ai-color-gray-100);
    color: var(--theme-ai-color-gray-900);
  }

  &.chip--verified {
    background-color: var(--theme-ai-color-green-100);
    color: var(--theme-ai-color-green-900);
  }

  &.chip--rejected {
    background-color: var(--theme-ai-color-red-100);
    color: var(--theme-ai-color-red-900);
  }

  &.chip--pending {
    background-color: var(--theme-ai-color-yellow-100);
    color: var(--theme-ai-color-yellow-900);
  }

  &.chip--new {
    background-color: var(--theme-ai-color-blue-100);
    color: var(--theme-ai-color-blue-900);
  }
}
</style>
