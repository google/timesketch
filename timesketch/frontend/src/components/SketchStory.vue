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
      <div class="container">
        <ts-navbar-secondary currentAppContext="sketch" currentPage="stories"></ts-navbar-secondary>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="card">
          <div class="card-content">

            <div class="columns">

              <div class="column">
                <div v-for="(obj, index) in blocks" :key="index">
                  <div v-if="!obj.component" style="margin-bottom: 10px;">
                    <textarea class="textarea" :value="obj.content" @input="update($event, obj)"></textarea>
                  </div>
                  <div v-if="obj.component" style="margin-bottom: 10px;">
                    <component :is="obj.component" v-bind="obj.props"></component>
                  </div>
                </div>
                <button v-on:click="addBlock">Add block</button>
              </div>

              <div class="column">
                <div v-for="(obj, index) in blocks" :key="`block-${index}`" style="padding:10px; margin:10px;">
                  <div v-if="obj.component">
                    <component :is="obj.component" v-bind="obj.props"></component>
                  </div>
                  <div v-if="obj.html" v-html="obj.html"></div>
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
import marked from 'marked'
import _ from 'lodash'
import SketchOverviewSummary from './SketchOverviewSummary'

export default {
  name: 'ts-sketch-story',
  components: { SketchOverviewSummary },
  data () {
    return {
      blocks: [
        {
          component: false,
          content: '',
          html: ''
        },
        {
          component: false,
          content: '',
          html: ''
        }
      ]
    }
  },
  methods: {
    update: _.debounce(function (e, obj) {
      obj.content = e.target.value
      obj.html = marked(e.target.value, { sanitize: false })
    }, 300),
    addBlock () {
      this.blocks.push({
        component: 'SketchOverviewSummary',
        props: { sketch: this.sketch },
        content: '',
        html: ''
      })
    },
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta () {
      return this.$store.state.meta
    },
    getProps () {
      return { sketch: this.sketch }
    }
  }
}
</script>

<style lang="scss"></style>
