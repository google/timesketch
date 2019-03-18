/*
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
*/
import Vue from 'vue'
import Vuex from 'vuex'
import ApiClient from './utils/RestApiClient'

Vue.use(Vuex)

const defaultState = () => {
  return {
    sketch: {},
    meta: {},
    count: 0,
    eventList: {
      meta: {},
      objects: []
    },
    currentQueryString: '',
    currentQueryFilter: {}
  }
}

// Initial state
const state = defaultState()

export default new Vuex.Store({
  state,
  mutations: {
    updateSketch (state, sketchId) {
      ApiClient.getSketch(sketchId).then((response) => {
        Vue.set(state, 'sketch', response.data.objects[0])
        Vue.set(state, 'meta', response.data.meta)
      }).catch((e) => {})

      // Count events for all timelines in the sketch
      ApiClient.countSketchEvents(sketchId).then((response) => {
        Vue.set(state, 'count', response.data.meta.count)
      }).catch((e) => {})
    },
    updateEventList (state, searchResult) {
      Vue.set(state, 'eventList', searchResult)
    },
    updateCurrentQueryString (state, queryString) {
      Vue.set(state, 'currentQueryString', queryString)
    },
    updateCurrentQueryFilter (state, queryFilter) {
      Vue.set(state, 'currentQueryFilter', queryFilter)
    },
    resetState (state) {
      Object.assign(state, defaultState())
    }
  },
  actions: {
    updateSketch (context, sketchId) {
      context.commit('updateSketch', sketchId)
    },
    updateEventList (context, searchResult) {
      context.commit('updateEventList', searchResult)
    },
    resetState (context) {
      context.commit('resetState')
    }
  }
})
