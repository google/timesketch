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
    <div v-on:click="setActiveView(view)" v-for="view in meta.views" :key="view.id" style="cursor:pointer; margin-bottom:10px;">
      {{ view.name }}
      <br>
      <span class="is-size-7">
        Created {{ view.created_at | moment("YYYY-MM-DD HH:mm") }} <span v-if="view.user"> by {{ view.user }}</span> <span v-if="view.description"> ({{ view.description }})</span>
      </span>
    </div>
  </div>
</template>

<script>
import ApiClient from '../../utils/RestApiClient'
import TsCreateViewForm from './CreateViewForm'

export default {
  components: {
    TsCreateViewForm
  },
  props: ['currentQueryString', 'currentQueryFilter', 'isSimple', 'isLast', 'sketchId'],
  data () {
    return {
      activeView: null,
      showCreateViewModal: false,
      position: 'is-bottom-right'
    }
  },
  methods: {
    setActiveView: function (view, doSearch = true) {
      this.showCreateViewModal = false
      this.activeView = view
      if (doSearch) {
        this.$emit('setActiveView', view)
      }
    },
    clearSearch: function () {
      this.$emit('clearSearch')
      this.activeView = null
      this.$refs.dropdown.toggle()
    },
    saveView: function () {
      this.showCreateViewModal = true
      this.$refs.dropdown.toggle()
    },
    updateView: function () {
      if (!this.activeView) {
        return
      }
      this.$refs.dropdown.toggle()
      this.activeView.query = this.currentQueryString
      this.activeView.filter = JSON.stringify(this.currentQueryFilter)
      ApiClient.updateView(this.sketchId, this.activeView.id, this.currentQueryString, this.currentQueryFilter)
        .then((response) => {
          this.$buefy.toast.open('Saved search has been updated')
        })
        .catch((e) => {})
    }
  },
  computed: {
    meta () {
      return this.$store.state.meta
    }
  },
  created: function () {
    if (this.isLast) {
      this.position = 'is-top-right'
    }
    let queryViewId = this.$route.query.view
    if (queryViewId) {
      let view = this.meta.views.filter(function (view) {
        return view.id === parseInt(queryViewId)
      })
      this.setActiveView(view[0], false)
    }
  }
}
</script>

<!-- CSS scoped to this component only -->
<style scoped lang="scss">
.button:focus, .button.is-focused {
  border-color: transparent;
}

.footer {
  background: #f5f5f5;
  border-top: solid 1px #d1d1d1;
  padding: 15px;
}

</style>
