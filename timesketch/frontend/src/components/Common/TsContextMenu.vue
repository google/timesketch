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
  <div class="context-menu" v-show="isOpen" ref="menuBox" :style="style">
    <slot :data="data" />
  </div>
</template>

<script>
export default {
  name: 'TsContextMenu',
  data() {
    return {
      isOpen: false,
      posX: 0,
      posY: 0,
      data: null,
      parentComponent: null,
    }
  },
  methods: {
    open(event, data, parentComponent) {
      this.close()
      if (event) {
        this.posX = event.clientX
        this.posY = event.clientY
      }

      this.data = data
      this.isOpen = true
      this.parentComponent = parentComponent
      document.addEventListener('click', this.handleClick)
    },

    close() {
      this.isOpen = false
      document.removeEventListener('click', this.handleClick)
    },

    handleClick(e) {
      // There's no context menu box or it's not open
      if (!this.$refs.menuBox || !this.isOpen) {
        return
      }

      // We want to make sure that clicks inside the menu box don't close it
      const insideClick = this.$refs.menuBox.contains(e.target)
      // We also want to make sure that clicks on the menu's parent component don't close it
      const highlightClick = this.parentComponent.contains(e.target)

      if (!(insideClick || highlightClick)) {
        this.close()
      }
    },
  },
  computed: {
    style() {
      return {
        left: `${this.posX}px`,
        top: `${this.posY}px`,
      }
    },
  },
}
</script>

<style scoped>
.context-menu {
  position: fixed;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
}
</style>
