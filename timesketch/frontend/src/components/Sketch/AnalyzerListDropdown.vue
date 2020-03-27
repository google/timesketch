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
    <b-dropdown position="is-bottom-left" aria-role="menu" trap-focus>
    <button class="button is-outlined is-rounded is-small" slot="trigger">
      <span class="icon is-small">
        <i class="fas fa-play-circle"></i>
      </span>
      <span>Analyze</span>
    </button>
    <b-dropdown-item aria-role="menu-item" :focusable="false" custom>
      <div class="modal-card" style="width:300px;">
        <div class="field" v-for="analyzer in sortedAnalyzerList()">
          <b-checkbox v-model="selectedAnalyzers" :native-value="analyzer" type="is-info">{{ analyzer }}</b-checkbox>
        </div>
        <button v-if="selectedAnalyzers.length" class="button is-success" v-on:click="runAnalyzers">Run</button>
      </div>
    </b-dropdown-item>
  </b-dropdown>

</template>

<script>
import ApiClient from '../../utils/RestApiClient'

export default {
  props: ['timeline'],
  data () {
    return {
      selectedAnalyzers: [],
    }
  },
  computed: {
    sketch () {
      return this.$store.state.sketch
    },
    meta() {
      return this.$store.state.meta
    }
  },
  methods: {
    sortedAnalyzerList: function () {
      const analyzerArrayCopy = [...this.$store.state.meta.analyzers];
      return analyzerArrayCopy.sort()
    },
    runAnalyzers: function () {
      ApiClient.runAnalyzers(this.sketch.id, this.timeline.id, this.selectedAnalyzers).then((response) => {
        this.$emit('newAnalysisSession', response.data.objects[0].analysis_session)
      }).catch((e) => {})
      this.selectedAnalyzers = []
    }
  }
}
</script>
