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
  <div style="max-height:700px;overflow:auto;overflow-x: hidden;border-radius:12px;">
    <div class="tile is-ancestor">
      <div class="tile is-vertical is-12">
        <div class="tile">
          <div class="tile is-parent is-vertical is-8" style="padding-right:0;">
            <div class="tile is-child">
              <div v-show="searchHistory.length < 2" style="padding:20px; border-radius:12px 0 0 0">
                <strong>Get started with these common queries</strong>
                <br />
                <div class="buttons">
                  <button class="button">
                    Windows logins
                  </button>
                  <button class="button">
                    Web browsing activity
                  </button>
                  <br /><br /><br /><br />
                  <b-message type="is-info">
                    <strong>Query format</strong>
                    <br />
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce id fermentum quam. Proin sagittis,
                    nibh id hendrerit imperdiet, elit sapien laoreet elit
                  </b-message>
                </div>
              </div>

              <div
                v-show="searchHistory.length > 1"
                style="padding:20px; border-radius:12px 0 0 0; background-color:#f5f5f5;"
              >
                <div class="buttons">
                  <span class="icon is-small" style="margin-right:5px;"><i class="fas fa-bolt"></i></span>
                  <strong style="margin-right:20px;">Quick links</strong>

                  <button
                    class="button is-text"
                    style="text-decoration:none;margin-top:5px;"
                    v-on:click="searchForLabel('__ts_star')"
                  >
                    <span style="margin-right:5px;" class="icon is-small"
                      ><i
                        class="fas fa-star"
                        style="color:#ffe300;-webkit-text-stroke-width: 1px;-webkit-text-stroke-color: silver;"
                      ></i
                    ></span>
                    All starred events
                  </button>

                  <button
                    class="button is-text"
                    style="text-decoration:none;margin-top:5px;"
                    v-on:click="searchForLabel('__ts_comment')"
                  >
                    <span style="margin-right:5px;" class="icon is-small"><i class="fas fa-comment"></i></span>
                    All commented events
                  </button>
                </div>
              </div>

              <div v-if="searchHistory.length" style="padding:20px 20px 20px 20px; border-top:1px solid #d3d3d3">
                <span class="icon is-small" style="margin-right:5px;"><i class="fas fa-history"></i></span>
                <strong>Recent searches</strong>
                <br /><br />
                <ts-recent-search-list
                  @node-click="$emit('node-click', $event)"
                  @close-on-click="$emit('close-on-click')"
                ></ts-recent-search-list>
              </div>

              <div v-show="searchHistory.length > 1" style="padding:20px; border-top:1px solid #d3d3d3;">
                <span class="icon is-small" style="margin-right:5px;"><i class="fas fa-database"></i></span>
                <strong>Data categories</strong>
                <br /><br />
                <div class="buttons">
                  <button
                    class="button"
                    v-for="dataType in dataTypes"
                    :key="dataType.data_type"
                    v-on:click="searchForDataType(dataType.data_type)"
                  >
                    {{ dataType.data_type }}
                    <b-tag style="margin-left:7px;">{{ dataType.count | compactNumber }}</b-tag>
                  </button>
                </div>
              </div>

              <div v-if="meta.filter_labels.length" style="padding:20px 20px 20px 20px; border-top:1px solid #d3d3d3">
                <span style="margin-right:5px;" class="icon is-small"><i class="fas fa-tags"></i></span>
                <strong>Tags</strong>
                <br /><br />
                <div class="buttons">
                  <button
                    class="button"
                    v-for="label in meta.filter_labels"
                    :key="label"
                    v-on:click="searchForLabel(label)"
                  >
                    {{ label }}
                  </button>
                  <button class="button" v-for="tag in tags" :key="tag.tag" v-on:click="searchForTag(tag.tag)">
                    {{ tag.tag }} <b-tag style="margin-left:7px;">{{ tag.count | compactNumber }}</b-tag>
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="tile is-parent" style="padding-left:0;">
            <div class="tile is-child">
              <div
                style="border-left:1px solid #d3d3d3; height:100%;background-color:#f5f5f5; border-radius:0 12px 12px 0;"
              >
                <div style="padding:20px 20px 0 20px;">
                  <span style="margin-right:5px;" class="icon is-small"><i class="fas fa-save"></i></span>
                  <strong>Saved searches</strong>
                  <br /><br />
                  <div v-if="!meta.views.length">No saved searches yet</div>
                </div>
                <ts-view-list :views="meta.views" @setActiveView="$emit('setActiveView', $event)"></ts-view-list>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TsViewList from '../Common/ViewListExplore'
import TsRecentSearchList from './RecentSearchList'

const defaultQueryFilter = () => {
  return {
    from: 0,
    terminate_after: 40,
    size: 40,
    indices: '_all',
    order: 'asc',
    chips: [],
  }
}

export default {
  components: {
    TsViewList,
    TsRecentSearchList,
  },
  props: ['selectedLabels'],
  computed: {
    sketch() {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    },
    searchHistory() {
      return this.$store.state.searchHistory
    },
    tags() {
      return this.$store.state.tags
    },
    dataTypes() {
      return this.$store.state.dataTypes
    },
  },
  beforeDestroy: function() {
    window.removeEventListener('click', this.close)
  },
  created: function() {
    window.addEventListener('click', this.close)
  },
  methods: {
    close(e) {
      if (!this.$el.contains(e.target)) {
        this.$emit('close', e.target)
      }
    },
    searchForLabel(label) {
      let eventData = {}
      eventData.queryString = '*'
      eventData.queryFilter = defaultQueryFilter()
      let chip = {
        field: '',
        value: label,
        type: 'label',
        operator: 'must',
        active: true,
      }
      eventData.queryFilter.chips.push(chip)
      this.$emit('setQueryAndFilter', eventData)
    },
    searchForTag(tag) {
      let eventData = {}
      eventData.queryString = 'tag:' + tag
      eventData.queryFilter = defaultQueryFilter()
      this.$emit('setQueryAndFilter', eventData)
    },
    searchForDataType(dataType) {
      let eventData = {}
      eventData.queryString = 'data_type:' + '"' + dataType + '"'
      eventData.queryFilter = defaultQueryFilter()
      this.$emit('setQueryAndFilter', eventData)
    },
  },
}
</script>
