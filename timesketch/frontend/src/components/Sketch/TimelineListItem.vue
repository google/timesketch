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

    <!-- Timeline detail modal -->
    <b-modal :active.sync="showInfoModal" :width="640" scroll="keep">
      <div class="modal-background"></div>
      <div class="modal-content">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Detailed information for {{ timeline.name }}</p>
          </header>
          <div class="card-content">
            <div class="content">
              <ul>
                <li>Elasticsearch index: {{ timeline.searchindex.index_name }}</li>
                <li>Original name: {{ timeline.searchindex.name }}</li>
                <li>Added by: {{ timeline.searchindex.user.username }}</li>
                <li>Added: {{ timeline.searchindex.created_at | moment("YYYY-MM-DD HH:mm") }}</li>
              </ul>
              <strong v-if="timeline.description">Description</strong>
              <p>{{ timeline.description}}</p>
            </div>
          </div>
        </div>
      </div>
      <button class="modal-close is-large" aria-label="close" v-on:click="showInfoModal = !showInfoModal"></button>
    </b-modal>

    <!-- Timeline edit modal -->
    <b-modal :active.sync="showEditModal" :width="640" scroll="keep">
      <div class="modal-background"></div>
      <div class="modal-content">
        <div class="card">
          <header class="card-header">
            <p class="card-header-title">Rename timeline</p>
          </header>
          <div class="card-content">
            <div class="content">
              <form v-on:submit.prevent="saveTimeline">
                <div class="field">
                  <div class="control">
                    <input v-model="timeline.name" class="input" type="text" required autofocus>
                  </div>
                </div>
                <div class="field">
                  <div class="control">
                    <input class="button is-success" type="submit" value="Save">
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
      <button class="modal-close is-large" aria-label="close" v-on:click="showEditModal = !showEditModal"></button>
    </b-modal>

    <div class="dropdown is-pulled-left" v-bind:class="{'is-active': colorPickerActive}">
      <div class="dropdown-trigger">
        <div class="ts-timeline-color-box" v-bind:style="timelineColorStyle" v-on:click="colorPickerActive = !colorPickerActive"></div>
      </div>
      <div class="dropdown-menu" id="dropdown-menu" role="menu">
        <div class="dropdown-content" style="padding:0;">
          <div class="dropdown-item" style="padding:0;">
            <color-picker v-model="initialColor" @input="updateColor"></color-picker>
          </div>
        </div>
      </div>
    </div>
    <div v-if="controls" class="field is-grouped is-pulled-right" style="margin-top:10px;">
      <p class="control">
        <button class="button is-rounded is-small is-outlined" v-on:click="showInfoModal = !showInfoModal">
                <span class="icon is-small">
                  <i class="fas fa-info-circle"></i>
                </span>
          <span>Info</span>
        </button>
      </p>
      <p class="control">
        <button class="button is-rounded is-small is-outlined" v-on:click="showEditModal = !showEditModal">
          <span class="icon is-small">
            <i class="fas fa-edit"></i>
          </span>
          <span>Rename</span>
        </button>
      </p>

      <p class="control">
        <ts-analyzer-list-dropdown :timeline="timeline" @newAnalysisSession="setAnalysisSession($event)"></ts-analyzer-list-dropdown>
      </p>

      <p class="control">
        <button class="button is-small is-rounded is-outlined" @click="showAnalysisHistory = !showAnalysisHistory">
          <span class="icon is-small">
            <i class="fas fa-history"></i>
          </span>
          <span>History</span>
        </button>
      </p>

      <p class="control">
        <button v-on:click="remove(timeline)" class="button is-small is-rounded is-danger is-outlined">Remove</button>
      </p>
    </div>
    <router-link :to="{ name: 'SketchExplore', query: {index: timeline.searchindex.index_name}}"><strong>{{ timeline.name }}</strong></router-link>
    <br>
    <span class="is-size-7">
      Added {{ timeline.updated_at | moment("YYYY-MM-DD HH:mm") }}
    </span>

    <br>

    <div v-show="analysisSessionId">
      <ts-analyzer-session-detail :timeline="timeline" :session-id="analysisSessionId" @sessionDone="analysisSessionId = false"></ts-analyzer-session-detail>
    </div>

    <div v-if="showAnalysisHistory">
      <ts-analyzer-history :timeline="timeline"></ts-analyzer-history>
    </div>

  </div>
</template>

<script>
import Vue from 'vue'
import { Chrome } from 'vue-color'
import _ from 'lodash'

import TsAnalyzerListDropdown from './AnalyzerListDropdown'
import TsAnalyzerSessionDetail from './AnalyzerSessionDetail'
import TsAnalyzerHistory from './AnalyzerHistory'

export default {
  components: {
    'color-picker': Chrome,
    TsAnalyzerListDropdown,
    TsAnalyzerSessionDetail,
    TsAnalyzerHistory
  },
  props: ['timeline', 'controls'],
  data () {
    return {
      initialColor: {},
      newColor: '',
      newTimelineName: '',
      colorPickerActive: false,
      showInfoModal: false,
      showEditModal: false,
      analysisSessionId: false,
      showAnalysisDetail: false,
      showAnalysisHistory: false
    }
  },
  computed: {
    timelineColorStyle () {
      let hexColor = this.newColor || this.timeline.color
      if (!hexColor.startsWith('#')) {
        hexColor = '#' + hexColor
      }
      return {
        'background-color': hexColor
      }
    }
  },
  methods: {
    remove (timeline) {
      this.$emit('remove', timeline)
    },
    updateColor: _.debounce(function (color) {
      this.newColor = color.hex
      if (this.newColor.startsWith('#')) {
        this.newColor = this.newColor.substring(1)
      }
      Vue.set(this.timeline, 'color', this.newColor)
      this.$emit('save', this.timeline)
    }, 300),
    saveTimeline () {
      this.showEditModal = false
      this.$emit('save', this.timeline)
    },
    setAnalysisSession (sessionId) {
      this.analysisSessionId = sessionId
      this.showAnalysisDetail = true
    }
  },
  mounted () {
    // Hide color picket when clicked outside.
    let self = this
    window.addEventListener('click', function (e) {
      if (!self.$el.contains(e.target)) {
        self.colorPickerActive = false
      }
    })
  },
  created () {
    this.initialColor = {
      hex: this.timeline.color
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.list-item {
  display: inline-block;
  margin-right: 10px;
}
.list-enter-active, .list-leave-active {
  transition: all 0.5s;
}
.list-enter, .list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
.vc-sketch {
  box-shadow: none;
}
</style>
