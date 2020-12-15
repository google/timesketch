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

  <div v-if="sketch.status">

    <ts-navbar-main>
      <template v-slot:left>
        {{ sketch.name }}
      </template>
    </ts-navbar-main>

    <div v-if="isArchived" class="task-container columns is-multiline" style="margin-top:50px;">
      <div class="card column is-half is-offset-one-quarter has-text-centered" style="min-height: 300px; padding-top: 90px;">
        <h4 class="title is-4">{{ sketch.name }}</h4>
        <p>This sketch has been archived</p>
        <div class="buttons is-centered" style="margin-top:30px">
          <button v-on:click="unArchiveSketch()" class="button is-success is-outlined">Unarchive</button>
          <button v-on:click="exportSketch()" class="button is-link is-outlined">Export</button>
        </div>
      </div>
    </div>

    <div v-if="!isArchived">
      <section class="section">
        <div class="container is-fluid">
          <ts-navbar-secondary currentAppContext="sketch" currentPage="overview">

            <span v-for="label in meta.sketch_labels" :key="label" style="margin-right:10px; color: var(--default-font-color);font-size: 0.7em">{{  label }}</span>

            <b-tooltip v-if="meta.collaborators" :label="shareTooltip" position="is-bottom" type="is-white">
              <a v-if="meta.permissions.write" class="button is-info" style="margin-right:10px;" v-on:click="showShareModal = !showShareModal">
                    <span class="icon is-small">
                      <i v-if="meta.permissions.public" class="fas fa-globe"></i>
                      <i v-else-if="meta.collaborators.users.length ||  meta.collaborators.groups.length" class="fas fa-users"></i>
                      <i v-else-if="!meta.permissions.public" class="fas fa-lock"></i>
                    </span>
                <span>Share</span>
              </a>
            </b-tooltip>

            <b-dropdown v-if="meta.permissions.write" aria-role="list" position="is-bottom-left">
              <a class="button ts-dropdown-button" style="background:transparent;border:none;" slot="trigger" slot-scope="{ active }">
                  <span class="icon is-small">
                    <i :class="active ? 'fas fa-angle-up' : 'fas fa-angle-down'"></i>
                  </span>
                <span>More</span>
              </a>
              <b-dropdown-item v-if="meta.permissions.delete" aria-role="listitem">
                <a class="dropdown-item" v-on:click="showDeleteSketchModal = !showDeleteSketchModal">
                  <span class="icon is-small" style="margin-right:5px;"><i class="fas fa-trash"></i></span>
                  <span>Delete</span>
                </a>
              </b-dropdown-item>
              <b-dropdown-item v-if="meta.permissions.delete" aria-role="listitem">
                <a class="dropdown-item" v-on:click="archiveSketch">
                  <span class="icon is-small" style="margin-right:5px;"><i class="fas fa-archive"></i></span>
                  <span>Archive</span>
                </a>
              </b-dropdown-item>
              <b-dropdown-item v-if="meta.permissions.read" aria-role="listitem">
                <a class="dropdown-item" v-on:click="exportSketch()">
                  <span class="icon is-small" style="margin-right:5px;"><i class="fas fa-file-export"></i></span>
                  <span>Export</span>
                </a>
              </b-dropdown-item>
            </b-dropdown>

          </ts-navbar-secondary>
        </div>
      </section>

      <b-modal :active.sync="showShareModal" :width="640" scroll="keep">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Share sketch</p>
          </header>
          <div class="card-content">
            <div class="content">
              <ts-share-form @closeShareModal="closeShareModal"></ts-share-form>
            </div>
          </div>
        </div>
      </b-modal>

      <b-modal :active.sync="showUploadTimelineModal" :width="640" scroll="keep">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Upload new timeline</p>
          </header>
          <div class="card-content">
            <div class="content">
              <p>
                Supported formats are Plaso storage file, JSONL, or a CSV file.
                If you are uploading a CSV or JSONL file make sure to read the <a href="https://github.com/google/timesketch/blob/master/docs/Users-Guide.md#adding-timelines" rel="noreferrer" target="_blank">documentation</a> to learn what columns are needed.
              </p>
              <ts-upload-timeline-form @toggleModal="showUploadTimelineModal = !showUploadTimelineModal"></ts-upload-timeline-form>
            </div>
          </div>
        </div>
      </b-modal>

      <b-modal :active.sync="showDeleteSketchModal" :width="640" scroll="keep">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Delete sketch</p>
          </header>
          <div class="card-content">
            <div class="content">
              <p>Are you sure you want to delete this sketch?</p>
              <div class="field is-grouped">
                <p class="control">
                  <button class="button is-danger" v-on:click="deleteSketch">
                    <span class="icon is-small" style="margin-right:5px;"><i class="fas fa-trash"></i></span>
                    <span>Delete</span>
                  </button>
                </p>
                <p class="control">
                  <button class="button" v-on:click="showDeleteSketchModal = !showDeleteSketchModal">
                    <span>I changed my mind, keep the sketch!</span>
                  </button>
                </p>
              </div>
            </div>
          </div>
        </div>
      </b-modal>

      <!-- Title and description -->
      <section class="section">
        <div class="container is-fluid">

          <div class="tile is-ancestor">
            <div class="tile is-8 is-parent">
              <div class="tile is-child tile-box">
                <div class="card-content">
                  <ts-sketch-summary :sketch="sketch"></ts-sketch-summary>
                  <br>
                  <b-field grouped group-multiline>
                    <div class="control" v-for="user in sortedUserList()" :key="user.name">
                      <b-tag attached size="is-medium">{{ user }}</b-tag>
                    </div>
                    <div class="control" v-for="group in sortedGroupList()" :key="group.name">
                      <b-tag attached size="is-medium">{{ group }}</b-tag>
                    </div>
                  </b-field>
                </div>
              </div>
            </div>
            <div class="tile is-parent">
              <div class="tile is-child tile-box">
                <header class="card-header">
                  <p class="card-header-title">Metadata</p>
                </header>
                <div style="padding:1.25em;">
                  Creator: {{ sketch.user.username }}
                </div>
              </div>
            </div>
          </div>

        </div>
      </section>

      <section class="section" v-if="sketch.active_timelines.length">
        <div class="container is-fluid">
          <div class="tile-box">
            <div style="padding:1.25em;">
              <ts-sketch-metrics :timelines="sketch.active_timelines" :views="meta.views" :stories="sketch.stories" :count="count"></ts-sketch-metrics>
            </div>
          </div>
        </div>
      </section>

      <!-- Timelines, Saved Views, Stories and Graphs lists-->
      <section class="section" v-if="sketch.timelines && sketch.timelines.length ? sketch.timelines.length: false">
        <div class="container is-fluid">

          <div class="tile is-ancestor">
            <div class="tile is-vertical is-12">
              <div class="tile">

                <div class="tile is-parent is-vertical">

                  <div class="tile is-child tile-box" v-if="sketch.timelines && sketch.timelines.length ? sketch.timelines.length: false">
                    <header class="card-header">
                      <p class="card-header-title">Timelines</p>
                      <div class="field is-grouped is-pulled-right" style="padding: 0.75rem;">
                        <p v-if="meta.permissions.write" class="control">
                          <button class="button is-success is-rounded is-small" v-on:click="showUploadTimelineModal = !showUploadTimelineModal">
                                <span class="icon is-small">
                                  <i class="fas fa-upload"></i>
                                </span>
                            <span>Upload timeline</span>
                          </button>
                        </p>
                        <p class="control">
                          <router-link class="button is-rounded is-small" :to="{ name: 'SketchManageTimelines' }">
                              <span class="icon is-small">
                                <i class="fas fa-cog"></i>
                              </span>
                            <span>Manage</span>
                          </router-link>
                        </p>
                      </div>
                    </header>
                    <div style="padding:1.25em;">
                      <ts-timeline-list :timelines="sketch.timelines" :controls="true" :is-compact="true"></ts-timeline-list>
                    </div>
                  </div>

                  <div class="tile is-child tile-box" v-if="sketch.stories.length">
                    <header class="card-header">
                      <p class="card-header-title">Stories</p>
                      <div class="field is-grouped is-pulled-right" style="padding: 0.75rem;">
                        <p class="control">
                          <router-link class="button is-rounded is-small is-success" :to="{ name: 'SketchStoryOverview' }">
                              <span class="icon is-small">
                                <i class="fas fa-plus-circle"></i>
                              </span>
                            <span>Create story</span>
                          </router-link>
                        </p>
                      </div>
                    </header>
                    <div style="padding:1.25em;">
                      <span v-if="!sketch.stories.length">No stories</span>
                      <ts-sketch-story-list :controls="false"></ts-sketch-story-list>
                    </div>
                  </div>
                </div>

                <div class="tile is-parent is-vertical">

                  <div class="tile is-child tile-box" v-if="!meta.views.length && !sketch.graphs.length">
                    <header class="card-header">
                      <p class="card-header-title">Get started!</p>
                      <div class="field is-grouped is-pulled-right" style="padding: 0.75rem;">
                      </div>
                    </header>
                    <div style="padding:1.25em;">
                      <p>
                        Welcome to your new investigation.
                        You get started by navigating to the <router-link style="text-decoration: underline;" :to="{ name: 'SketchExplore' }">explore page</router-link> where you can navigate your timelines, use search queries,
                        apply filters, view timeline data and save your search discoveries as new saved searches.
                      </p>
                      <br>
                      <router-link class="button is-success" :to="{ name: 'SketchExplore' }">
                        <span>Begin to explore your data</span>
                        <span class="icon is-small">
                          <i class="fas fa-chevron-circle-right"></i>
                        </span>
                      </router-link>
                    </div>
                  </div>

                  <div class="tile is-child tile-box" v-if="meta.views.length">
                    <header class="card-header">
                      <p class="card-header-title">Saved searches</p>
                      <div class="field is-grouped is-pulled-right" style="padding: 0.75rem;">
                        <p class="control" v-if="sketch.stories.length">
                          <router-link class="button is-rounded is-small" :to="{ name: 'SketchManageViews' }">
                            <span class="icon is-small">
                              <i class="fas fa-cog"></i>
                            </span>
                            <span>Manage</span>
                          </router-link>
                        </p>
                      </div>
                    </header>
                    <div style="padding:1.25em;">
                      <span v-if="!meta.views.length">No saved searches</span>
                      <ts-saved-view-list :views="meta.views"></ts-saved-view-list>
                    </div>
                  </div>

                  <div class="tile is-child tile-box" v-if="sketch.graphs.length">
                    <header class="card-header">
                      <p class="card-header-title">Saved graphs</p>
                      <div class="field is-grouped is-pulled-right" style="padding: 0.75rem;">
                        <p class="control">
                          <router-link class="button is-rounded is-small is-success" :to="{ name: 'SketchGraphOverview' }">
                            <span>Explore all graphs</span>
                            <span class="icon is-small">
                              <i class="fas fa-chevron-circle-right"></i>
                            </span>
                          </router-link>
                        </p>
                      </div>
                    </header>
                    <div style="padding:1.25em;">
                      <ts-graph-list></ts-graph-list>
                    </div>
                  </div>

                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <ts-sketch-timelines-manage v-if="!sketch.timelines.length" :hide-navigation="true"></ts-sketch-timelines-manage>

    </div>
  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import TsSketchSummary from '../components/Sketch/SketchSummary'
import TsSketchMetrics from '../components/Sketch/SketchMetrics'
import TsTimelineList from '../components/Sketch/TimelineList'
import TsSavedViewList from '../components/Sketch/ViewList'
import TsSketchStoryList from '../components/Sketch/StoryList'
import TsUploadTimelineForm from '../components/Sketch/UploadForm'
import TsSketchTimelinesManage from './SketchManageTimelines'
import TsShareForm from '../components/Sketch/ShareForm'
import SessionChart from "../components/Sketch/SessionChart"
import TsGraphList from "../components/Sketch/GraphList"


export default {
  components: {
    SessionChart,
    TsSketchMetrics,
    TsSketchSummary,
    TsTimelineList,
    TsSavedViewList,
    TsUploadTimelineForm,
    TsSketchStoryList,
    TsSketchTimelinesManage,
    TsShareForm,
    TsGraphList
  },
  data () {
    return {
      showUploadTimelineModal: false,
      showDeleteSketchModal: false,
      showShareModal: false,
      isFullPage: true,
      loadingComponent: null,
      isArchived: false
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    },
    count () {
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
    }
  },
  methods: {
    deleteSketch: function () {
      ApiClient.deleteSketch(this.sketch.id).then((response) => {
        this.$router.push({ name: 'Home' })
      }).catch((e) => {
        console.error(e)
      })
    },
    archiveSketch: function () {
      this.isArchived = true
      ApiClient.archiveSketch(this.sketch.id).then((response) => {
        this.$store.dispatch('updateSketch', this.sketch.id)
        this.$router.push({ name: 'SketchOverview', params: { sketchId: this.sketch.id } })
      }).catch((e) => {
        console.error(e)
      })
    },
    unArchiveSketch: function () {
      this.isArchived = false
      ApiClient.unArchiveSketch(this.sketch.id).then((response) => {
        this.$store.dispatch('updateSketch', this.sketch.id)
        this.$router.push({ name: 'SketchOverview', params: { sketchId: this.sketch.id } })
      }).catch((e) => {
        console.error(e)
      })
    },
    exportSketch: function () {
      this.loadingOpen()
      ApiClient.exportSketch(this.sketch.id).then((response) => {
        let fileURL = window.URL.createObjectURL(new Blob([response.data]));
        let fileLink = document.createElement('a');
        let fileName = 'sketch-' + this.sketch.id + '-export.zip'
        fileLink.href = fileURL;
        fileLink.setAttribute('download', fileName);
        document.body.appendChild(fileLink);
        fileLink.click();
        this.loadingClose()
      }).catch((e) => {
        console.error(e)
        this.loadingClose()
      })
    },
    sortedUserList: function () {
      const userArrayCopy = [...this.$store.state.meta.collaborators.users];
      return userArrayCopy.sort()
    },
    sortedGroupList: function () {
      const groupArrayCopy = [...this.$store.state.meta.collaborators.groups];
      return groupArrayCopy.sort()
    },
    closeShareModal: function () {
      this.showShareModal = false
      this.$buefy.snackbar.open({
        duration: 3500,
        message: 'Sharing settings have been saved',
        type: 'is-white',
        position: 'is-top',
        queue: false
      })
      this.$store.dispatch('updateSketch', this.sketch.id)
    },
    loadingOpen: function () {
      this.loadingComponent = this.$buefy.loading.open({
        container: this.isFullPage ? null : this.$refs.element.$el
      })
    },
    loadingClose: function () {
      this.loadingComponent.close()
    }
  },
  created: function () {
    if (this.sketch.status[0].status === 'archived') {
      this.isArchived = true
    }
  }
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
    border: 1px solid red;
  }
  .archive-card.is-wide {
    width: 520px;
    height: 350px;
    padding-top:30px;
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


</style>
