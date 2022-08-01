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
    <ts-navbar-main v-if="!hideNavigation">
      <template v-slot:left>
        {{ sketch.name }}
      </template>
    </ts-navbar-main>

    <ts-navbar-secondary
      v-if="!hideNavigation"
      currentAppContext="sketch"
      currentPage="timelines"
    ></ts-navbar-secondary>

    <!-- Timelines to add -->
    <section v-if="meta.permissions.write" class="section">
      <div class="container is-fluid">
        <div class="card" style="min-height:160px;">
          <header class="card-header">
            <p class="card-header-title">Upload timeline</p>
          </header>
          <div class="card-content">
            <b-message>
              <p>
                Upload a new timeline or choose an existing one from the list below. You can upload either a Plaso
                storage file, JSONL, or a CSV file.
                <br />
                If you are uploading a CSV or JSONL file make sure to read the
                <a
                  href="https://timesketch.org/guides/user/import-from-json-csv/"
                  rel="noreferrer"
                  target="_blank"
                  >documentation</a
                >
                to learn what columns are needed.
              </p>
              <br />
              <ts-upload-timeline-form></ts-upload-timeline-form>
            </b-message>
          </div>
        </div>
      </div>
    </section>

    <!-- Active Timelines -->
    <section class="section" v-if="sketch.timelines.length">
      <div class="container is-fluid">
        <div class="card" style="min-height:160px;">
          <header class="card-header">
            <p class="card-header-title">Active Timelines</p>
            <p class="is-pulled-right" style="padding: 0.75rem;font-weight: bold;color: #777777;">
              {{ count | compactNumber }} events
            </p>
          </header>
          <div class="card-content">
            <ts-timeline-list :timelines="sketch.timelines" :controls="true"></ts-timeline-list>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import TsTimelineList from '../components/Timelines/TimelineList'
import TsUploadTimelineForm from '../components/Common/UploadForm'

export default {
  components: {
    TsTimelineList,
    TsUploadTimelineForm,
  },
  props: ['hideNavigation'],
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
  },
}
</script>

<style lang="scss"></style>
