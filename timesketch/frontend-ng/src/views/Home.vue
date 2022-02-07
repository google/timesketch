<!--
Copyright 2019 Google Inc. All rights reserved.

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
  <div>
    <v-row>
      <v-col cols="12">
        <v-sheet outlined rounded>
          <ts-sketch-list scope="recent"></ts-sketch-list>
        </v-sheet>
      </v-col>
      <v-col cols="12">
        <v-sheet outlined rounded>
          <ts-sketch-list scope="user"></ts-sketch-list>
        </v-sheet>
      </v-col>
    </v-row>
  </div>
</template>

<script>
export default {
  components: {},
  data() {
    return {
      showSketchCreateModal: false,
      allSketches: [],
      mySketches: [],
      myArchivedSketches: [],
      sharedSketches: [],
      loading: true,
      isFullPage: true,
      loadingComponent: null,
      searchQuery: '',
      newSearchQuery: '',
    }
  },
  computed: {
    filteredList() {
      return this.allSketches.filter((sketch) => {
        return sketch.name.toLowerCase().includes(this.search.toLowerCase())
      })
    },
  },
  methods: {
    loadingOpen: function () {
      this.loading = true
      this.loadingComponent = this.$buefy.loading.open({
        container: this.isFullPage ? null : this.$refs.element.$el,
      })
    },
    loadingClose: function () {
      this.loading = false
      this.loadingComponent.close()
    },
    search: function () {
      this.newSearchQuery = this.searchQuery
    },
  },
  created: function () {
    this.$store.dispatch('resetState')
    document.title = 'Timesketch'
  },
}
</script>
