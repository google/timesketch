<!--
Copyright 2021 Google Inc. All rights reserved.

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
  <b-dropdown :position="position" append-to-body aria-role="menu">
    <span slot="trigger">
      <slot name="dropdown-trigger-element"></slot>
    </span>
    <div
      style="border-radius:6px;background-color:var(--dropdown-background-color);color:var(--default-font-color);padding:16px;border: 1px solid var(--table-cell-border-color);"
      :style="dropdownWidth"
    >
      <b-dropdown-item paddingless custom :focusable="false" style="color:var(--default-font-color);">
        <slot></slot>
      </b-dropdown-item>
    </div>
  </b-dropdown>
</template>

<script>
export default {
  props: {
    width: {
      default: '300px',
      type: String,
    },
    position: {
      default: 'is-bottom-right',
      type: String,
    },
  },
  computed: {
    dropdownWidth() {
      let style = {
        width: this.width,
      }
      return style
    },
  },
}
</script>
