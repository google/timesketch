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

<!--
 Canvas is a routing component to keep views alive and to support communication between
 them via Eventbus.
-->
<template>
  <v-snackbar v-model="isVisible" :timeout="4000" :color="notification?.type" class="rounded-m">
    <div class="d-flex align-center">
      <v-icon :icon="notification?.icon" class="mr-2" />
      <p>{{ notification?.text }}</p>
    </div>
  </v-snackbar>
</template>

<script setup>
import { useAppStore } from "@/stores/app";
import { computed } from "vue";

const store = useAppStore();
const isVisible = ref(false);
const notification = computed(() => store.notification);

watch(notification, async () => {
  isVisible.value = true;
});
</script>
