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

    <section class="section">
      <div class="container is-fluid">
        <ts-navbar-secondary currentAppContext="sketch" currentPage="stories"></ts-navbar-secondary>
      </div>
    </section>

    <section class="section" v-if="blocks">
      <div class="container is-fluid">
        <div class="card">
          <div class="card-content" style="padding:50px;">

            <div class="markdown-body ts-markdown-body-color" style="margin-bottom:20px;padding-left:10px">
              <h1>{{ title }}</h1>
            </div>

            <div v-for="(obj, index) in blocks" :key="index">

              <div v-if="!obj.componentName" @mouseover="obj.isActive = true" @mouseleave="obj.isActive = false" v-bind:class="{ activeBlock: obj.isActive }" class="inactiveBlock" style="padding-left:10px;">

                <span v-if="obj.isActive" style="float:right;">
                  <button class="delete" v-on:click="deleteBlock(index)"></button>
                </span>

                <div class="columns" v-if="obj.edit" style="margin-bottom:0;">
                  <div class="column">
                    <textarea class="textarea" style="height: 100%;" :value="obj.content" @input="update($event, obj)" placeholder="Your story starts here.."></textarea>
                  </div>
                  <transition name="fade">
                    <div class="column" v-if="obj.content">
                      <div v-html="toHtml(obj.content)" class="markdown-body" style="max-height: 600px;overflow: auto;"></div>
                    </div>
                  </transition>
                </div>
                <div v-if="obj.edit" class="field is-grouped">
                  <p class="control">
                    <button :disabled="!obj.content" class="button is-rounded is-success" v-on:click="saveAndHide(obj)">
                      <span class="icon is-small"><i class="fas fa-save" aria-hidden="true"></i></span>
                      <span>Save</span>
                    </button>
                  </p>
                </div>
                <div v-on:dblclick="obj.edit = !obj.edit" class="markdown-body" v-if="!obj.edit" v-html="toHtml(obj.content)"></div>
              </div>

              <div v-if="obj.componentName" @mouseover="obj.isActive = true" @mouseleave="obj.isActive = false">
                <article class="message">
                  <div class="message-header">
                    <p v-if="obj.componentName === 'TsViewEventList'">
                      <router-link :to="{ name: 'SketchExplore', query: {view: obj.componentProps.view.id}}"><strong>{{ obj.componentProps.view.name }}</strong></router-link>
                    </p>
                    <p v-if="obj.componentName === 'TsAggregationCompact'">
                      {{ obj.componentProps.aggregation.name }}
                    </p>
                    <p v-if="obj.componentName === 'TsAggregationGroupCompact'">
                      {{ obj.componentProps.aggregation_group.name }}
                    </p>
                    <button class="delete" aria-label="delete" v-on:click="deleteBlock(index)"></button>
                  </div>
                  <div class="message-body">
                    <component :is="obj.componentName" v-bind="obj.componentProps"></component>
                  </div>
                </article>
              </div>

              <div style="min-height:35px;margin-top:10px;margin-bottom:10px;" @mouseover="obj.showPanel = true" @mouseleave="obj.showPanel = false">
                <div v-if="index === blocks.length - 1" style="padding-top:20px;"></div>
                  <div v-if="index === blocks.length - 1 || obj.showPanel || obj.isActive" class="field is-grouped">
                    <p class="control">
                      <button class="button is-rounded" v-on:click="addBlock(index)">
                        + Text
                      </button>
                    </p>
                    <p class="control" v-if="meta.views.length">
                      <ts-view-list-dropdown @setActiveView="addViewComponent($event, index)" :is-rounded="true" :is-small="false" :title="'+ Saved search'"></ts-view-list-dropdown>
                    </p>
                    <p class="control" v-if="allAggregations">
                      <ts-aggregation-list-dropdown @addAggregation="addAggregationComponent($event, index)" :is-rounded="true" :title="'+ Aggregation'" :aggregations="allAggregations" ></ts-aggregation-list-dropdown>
                    </p>
                  </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </section>

  </div>
</template>

<script>
import ApiClient from '../utils/RestApiClient'
import marked from 'marked'
import _ from 'lodash'
import TsAggregationListDropdown from '../components/Sketch/AggregationListDropdown'
import TsAggregationCompact from "../components/Sketch/AggregationCompact"
import TsAggregationGroupCompact from "../components/Sketch/AggregationGroupCompact"
import TsViewListDropdown from '../components/Sketch/ViewListDropdown'
import TsViewEventList from '../components/Sketch/EventListCompact'

const defaultBlock = () => {
  return {
    componentName: '',
    componentProps: {},
    content: '',
    edit: true,
    showPanel: false,
    isActive: false
  }
}

export default {
  components: { TsAggregationListDropdown, TsAggregationCompact, TsAggregationGroupCompact, TsViewListDropdown, TsViewEventList },
  props: ['sketchId', 'storyId'],
  data () {
    return {
      blocks: [],
      title: '',
      aggregations: [],
      aggregationGroups: []
    }
  },
  methods: {
    update: _.debounce(function (e, obj) {
      obj.content = e.target.value
      this.save()
    }, 300),
    addBlock (index) {
      let newIndex = index + 1
      let newBlock = defaultBlock()
      this.blocks.splice(newIndex, 0, newBlock)
    },
    deleteBlock (index) {
      this.blocks.splice(index, 1)
      if (!this.blocks.length) {
        this.blocks = [defaultBlock()]
      }
      this.save()
    },
    addAggregationComponent (event, index) {
      let newIndex = index + 1
      let newBlock = defaultBlock()
      // If object has an agg_ids key it is an aggregation group.
      if ('agg_ids' in event) {
        newBlock.componentName = 'TsAggregationGroupCompact'
        newBlock.componentProps = { aggregation_group: event }
      } else {
        newBlock.componentName = 'TsAggregationCompact'
        newBlock.componentProps = { aggregation: event }
      }
      this.blocks.splice(newIndex, 0, newBlock)
      this.save()
    },
    addViewComponent (event, index) {
      let newIndex = index + 1
      let newBlock = defaultBlock()
      newBlock.componentName = 'TsViewEventList'
      newBlock.componentProps = { view: event }
      this.blocks.splice(newIndex, 0, newBlock)
      this.save()
    },
    hideBlock (block) {
      block.edit = !block.edit
    },
    saveAndHide (block) {
      this.hideBlock(block)
      this.save()
    },
    save () {
      this.blocks.forEach(function (block) {
        block.showPanel = false
        block.isActive = false
      })
      let content = JSON.stringify(this.blocks)
      ApiClient.updateStory(this.title, content, this.sketchId, this.storyId)
        .then((response) => {
        }).catch((e) => {})
    },
    toHtml (markdown) {
      return marked(markdown, { sanitize: false })
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    },
    allAggregations () {
      const concat = (...arrays) => [].concat(...arrays.filter(Array.isArray));
      return concat(this.aggregations, this.aggregationGroups)
    }
  },
  created: function () {
    ApiClient.getStory(this.sketchId, this.storyId).then((response) => {
      this.title = response.data.objects[0].title
      let content = response.data.objects[0].content
      if (content === '[]') {
        this.blocks = [defaultBlock()]
      } else {
        this.blocks = JSON.parse(content)
      }
    }).catch((e) => {
      console.error(e)
    })
    ApiClient.getAggregations(this.sketchId).then((response) => {
      this.aggregations = response.data.objects[0]
    }).catch((e) => {
      console.error(e)
    })
    ApiClient.getAggregationGroups(this.sketchId).then((response) => {
      this.aggregationGroups = response.data.objects
    }).catch((e) => {
      console.error(e)
    })
  }
}
</script>

<style lang="scss">

.inactiveBlock {
  border-left: 1px solid transparent;
}

.activeBlock {
  border-left: 1px solid lightgray;
}

// Transition animation
.fade-enter-active, .fade-leave-active {
  transition: opacity .5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}

// Based on https://github.com/sindresorhus/github-markdown-css (MIT License)
.markdown-body {
  -ms-text-size-adjust: 100%;
  -webkit-text-size-adjust: 100%;
  line-height: 1.5;
  font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol;
  font-size: 16px;
  line-height: 1.5;
  word-wrap: break-word;
  max-width: 75ch;
}

.markdown-body details {
  display: block;
}

.markdown-body summary {
  display: list-item;
}

.markdown-body a {
  background-color: transparent;
}

.markdown-body a:active,
.markdown-body a:hover {
  outline-width: 0;
}

.markdown-body strong {
  font-weight: inherit;
  font-weight: bolder;
}

.markdown-body h1 {
  font-size: 2em;
  margin: .67em 0;
}

.markdown-body img {
  border-style: none;
}

.markdown-body code,
.markdown-body kbd,
.markdown-body pre {
  font-family: monospace,monospace;
  font-size: 1em;
}

.markdown-body hr {
  box-sizing: content-box;
  height: 0;
  overflow: visible;
}

.markdown-body input {
  font: inherit;
  margin: 0;
}

.markdown-body input {
  overflow: visible;
}

.markdown-body [type=checkbox] {
  box-sizing: border-box;
  padding: 0;
}

.markdown-body * {
  box-sizing: border-box;
}

.markdown-body input {
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
}

.markdown-body a {
  color: #0366d6;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body strong {
  font-weight: 600;
}

.markdown-body hr {
  background: transparent;
  border: 0;
  border-bottom: 1px solid #dfe2e5;
  height: 0;
  margin: 15px 0;
  overflow: hidden;
}

.markdown-body hr:before {
  content: "";
  display: table;
}

.markdown-body hr:after {
  clear: both;
  content: "";
  display: table;
}

.markdown-body table {
  border-collapse: collapse;
  border-spacing: 0;
}

.markdown-body td,
.markdown-body th {
  padding: 0;
}

.markdown-body details summary {
  cursor: pointer;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin-bottom: 0;
  margin-top: 0;
}

.markdown-body h1 {
  font-size: 32px;
}

.markdown-body h1,
.markdown-body h2 {
  font-weight: 600;
}

.markdown-body h2 {
  font-size: 24px;
}

.markdown-body h3 {
  font-size: 20px;
}

.markdown-body h3,
.markdown-body h4 {
  font-weight: 600;
}

.markdown-body h4 {
  font-size: 16px;
}

.markdown-body h5 {
  font-size: 14px;
}

.markdown-body h5,
.markdown-body h6 {
  font-weight: 600;
}

.markdown-body h6 {
  font-size: 12px;
}

.markdown-body p {
  margin-bottom: 10px;
  margin-top: 0;
}

.markdown-body blockquote {
  margin: 0;
}

.markdown-body ol,
.markdown-body ul {
  margin-bottom: 0;
  margin-top: 0;
  padding-left: 0;
}

.markdown-body ol ol,
.markdown-body ul ol {
  list-style-type: lower-roman;
}

.markdown-body ol ol ol,
.markdown-body ol ul ol,
.markdown-body ul ol ol,
.markdown-body ul ul ol {
  list-style-type: lower-alpha;
}

.markdown-body dd {
  margin-left: 0;
}

.markdown-body code,
.markdown-body pre {
  font-family: SFMono-Regular,Consolas,Liberation Mono,Menlo,Courier,monospace;
  font-size: 12px;
}

.markdown-body pre {
  margin-bottom: 0;
  margin-top: 0;
}

.markdown-body input::-webkit-inner-spin-button,
.markdown-body input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  appearance: none;
  margin: 0;
}

.markdown-body:before {
  content: "";
  display: table;
}

.markdown-body:after {
  clear: both;
  content: "";
  display: table;
}

.markdown-body>:first-child {
  margin-top: 0!important;
}

.markdown-body>:last-child {
  margin-bottom: 0!important;
}

.markdown-body a:not([href]) {
  color: inherit;
  text-decoration: none;
}

.markdown-body blockquote,
.markdown-body dl,
.markdown-body ol,
.markdown-body p,
.markdown-body pre,
.markdown-body table,
.markdown-body ul {
  margin-bottom: 16px;
  margin-top: 0;
}

.markdown-body hr {
  background-color: #e1e4e8;
  border: 0;
  height: .25em;
  margin: 24px 0;
  padding: 0;
}

.markdown-body blockquote {
  border-left: .25em solid #dfe2e5;
  color: #6a737d;
  padding: 0 1em;
}

.markdown-body blockquote>:first-child {
  margin-top: 0;
}

.markdown-body blockquote>:last-child {
  margin-bottom: 0;
}

.markdown-body kbd {
  background-color: #fafbfc;
  border: 1px solid #c6cbd1;
  border-bottom-color: #959da5;
  border-radius: 3px;
  box-shadow: inset 0 -1px 0 #959da5;
  color: #444d56;
  display: inline-block;
  font-size: 11px;
  line-height: 10px;
  padding: 3px 5px;
  vertical-align: middle;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  font-weight: 600;
  line-height: 1.25;
  margin-bottom: 16px;
  margin-top: 24px;
}

.markdown-body h1 {
  font-size: 2em;
}

.markdown-body h1,
.markdown-body h2 {
  padding-bottom: .3em;
}

.markdown-body h2 {
  font-size: 1.5em;
}

.markdown-body h3 {
  font-size: 1.25em;
}

.markdown-body h4 {
  font-size: 1em;
}

.markdown-body h5 {
  font-size: .875em;
}

.markdown-body h6 {
  color: #6a737d;
  font-size: .85em;
}

.markdown-body ol,
.markdown-body ul {
  padding-left: 2em;
}

.markdown-body ol ol,
.markdown-body ol ul,
.markdown-body ul ol,
.markdown-body ul ul {
  margin-bottom: 0;
  margin-top: 0;
}

.markdown-body li {
  word-wrap: break-all;
}

.markdown-body li>p {
  margin-top: 16px;
}

.markdown-body li+li {
  margin-top: .25em;
}

.markdown-body dl {
  padding: 0;
}

.markdown-body dl dt {
  font-size: 1em;
  font-style: italic;
  font-weight: 600;
  margin-top: 16px;
  padding: 0;
}

.markdown-body dl dd {
  margin-bottom: 16px;
  padding: 0 16px;
}

.markdown-body table {
  display: block;
  overflow: auto;
  width: 100%;
}

.markdown-body table th {
  font-weight: 600;
}

.markdown-body table td,
.markdown-body table th {
  border: 1px solid #dfe2e5;
  padding: 6px 13px;
}

.markdown-body table tr {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

.markdown-body table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

.markdown-body img {
  background-color: #fff;
  box-sizing: content-box;
  max-width: 100%;
}

.markdown-body img[align=right] {
  padding-left: 20px;
}

.markdown-body img[align=left] {
  padding-right: 20px;
}

.markdown-body code {
  background-color: rgba(27,31,35,.05);
  border-radius: 3px;
  font-size: 85%;
  margin: 0;
  padding: .2em .4em;
}

.markdown-body pre {
  word-wrap: normal;
}

.markdown-body pre>code {
  background: transparent;
  border: 0;
  font-size: 100%;
  margin: 0;
  padding: 0;
  white-space: pre;
  word-break: normal;
}

.markdown-body pre {
  background-color: #f6f8fa;
  border-radius: 3px;
  font-size: 85%;
  line-height: 1.45;
  overflow: auto;
  padding: 16px;
}

.markdown-body pre code {
  background-color: transparent;
  border: 0;
  display: inline;
  line-height: inherit;
  margin: 0;
  max-width: auto;
  overflow: visible;
  padding: 0;
  word-wrap: normal;
}

.markdown-body kbd {
  background-color: #fafbfc;
  border: 1px solid #d1d5da;
  border-bottom-color: #c6cbd1;
  border-radius: 3px;
  box-shadow: inset 0 -1px 0 #c6cbd1;
  color: #444d56;
  display: inline-block;
  font: 11px SFMono-Regular,Consolas,Liberation Mono,Menlo,Courier,monospace;
  line-height: 10px;
  padding: 3px 5px;
  vertical-align: middle;
}

.markdown-body hr {
  border-bottom-color: #eee;
}

</style>
