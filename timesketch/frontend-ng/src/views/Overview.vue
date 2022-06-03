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
  <v-container fluid>
    <v-row>
      <v-col cols="6">
        <v-card>
          <ts-timelines-table></ts-timelines-table>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="6">
        <v-card>
          <ts-search-history-table></ts-search-history-table>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="6">
        <v-card>
          <ts-saved-searches-table></ts-saved-searches-table>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="6">
        <v-card>
          <ts-data-types-table></ts-data-types-table>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="6">
        <v-card>
          <ts-tags-table></ts-tags-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import TsTimelinesTable from '../components/TimelinesTable'
import TsDataTypesTable from '../components/DataTypesTable'
import TsTagsTable from '../components/TagsTable'
import TsSearchHistoryTable from '../components/SearchHistoryTable'
import TsSavedSearchesTable from '../components/SavedSearchesTable'
import ApiClient from '../utils/RestApiClient'

export default {
  components: { TsTimelinesTable, TsDataTypesTable, TsTagsTable, TsSearchHistoryTable, TsSavedSearchesTable },
  data() {
    return {
      showUploadTimelineModal: false,
      showDeleteSketchModal: false,
      showShareModal: false,
      isFullPage: true,
      loadingComponent: null,
      isArchived: false,
    }
  },
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    count() {
      return this.$store.state.count
    },
    shareTooltip: function () {
      let msg = ''
      let baseMsg = 'Shared with '
      if (this.meta.collaborators.users.length) {
        msg = baseMsg + this.meta.collaborators.users.length + ' users'
        if (this.meta.collaborators.groups.length) {
          msg = msg + ' and ' + this.meta.collaborators.groups.length + ' groups'
        }
      }
      if (!msg && this.meta.collaborators.groups.length) {
        msg = baseMsg + this.meta.collaborators.groups.length + ' groups'
      }
      return msg
    },
  },
  methods: {
    deleteSketch: function () {
      ApiClient.deleteSketch(this.sketch.id)
        .then((response) => {
          this.$router.push({ name: 'Home' })
        })
        .catch((e) => {
          console.error(e)
        })
    },
    archiveSketch: function () {
      this.isArchived = true
      ApiClient.archiveSketch(this.sketch.id)
        .then((response) => {
          this.$store.dispatch('updateSketch', this.sketch.id)
          this.$router.push({ name: 'Overview', params: { sketchId: this.sketch.id } })
        })
        .catch((e) => {
          console.error(e)
        })
    },
    unArchiveSketch: function () {
      this.isArchived = false
      ApiClient.unArchiveSketch(this.sketch.id)
        .then((response) => {
          this.$store.dispatch('updateSketch', this.sketch.id)
          this.$router.push({ name: 'Overview', params: { sketchId: this.sketch.id } })
        })
        .catch((e) => {
          console.error(e)
        })
    },
    exportSketch: function () {
      this.loadingOpen()
      ApiClient.exportSketch(this.sketch.id)
        .then((response) => {
          let fileURL = window.URL.createObjectURL(new Blob([response.data]))
          let fileLink = document.createElement('a')
          let fileName = 'sketch-' + this.sketch.id + '-export.zip'
          fileLink.href = fileURL
          fileLink.setAttribute('download', fileName)
          document.body.appendChild(fileLink)
          fileLink.click()
          this.loadingClose()
        })
        .catch((e) => {
          console.error(e)
          this.loadingClose()
        })
    },
    sortedUserList: function () {
      const userArrayCopy = [...this.$store.state.meta.collaborators.users]
      return userArrayCopy.sort()
    },
    sortedGroupList: function () {
      const groupArrayCopy = [...this.$store.state.meta.collaborators.groups]
      return groupArrayCopy.sort()
    },
    closeShareModal: function () {
      this.showShareModal = false
      this.$buefy.snackbar.open({
        duration: 3500,
        message: 'Sharing settings have been saved',
        type: 'is-white',
        position: 'is-top',
        queue: false,
      })
      this.$store.dispatch('updateSketch', this.sketch.id)
    },
    loadingOpen: function () {
      this.loadingComponent = this.$buefy.loading.open({
        container: this.isFullPage ? null : this.$refs.element.$el,
      })
    },
    loadingClose: function () {
      this.loadingComponent.close()
    },
  },
  created: function () {
    if (this.sketch.status[0].status === 'archived') {
      this.isArchived = true
    }
  },
}
</script>

<style lang="scss">
.has-min-height {
  min-height: 300px;
}
.center-container {
  display: flex;
  height: 100%;
  width: 100%;
  align-items: center;
  justify-content: center;
}
.archive-card.is-wide {
  width: 520px;
  height: 350px;
  padding-top: 30px;
}
.archive-card.has-text-centered,
.archive-card-content {
  justify-content: center;
  align-items: center;
}

.tile-box {
  border-radius: 6px;
  background-color: var(--card-background-color);
  color: var(--default-font-color);
}

.block-condensed:not(:last-child) {
  margin-bottom: 0.5rem;
}
</style>
