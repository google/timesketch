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
  ApiClient.getLoggedInUser().then((response) => {
    let user = response.data.objects[0].username
    return {
      sketch: {},
      meta: {},
      count: 0,
      user: user
    }
  }).catch((e) => {})
}

// Initial state
const state = defaultState()

export default new Vuex.Store({
  state,
  mutations: {
    SET_SKETCH (state, payload) {
      Vue.set(state, 'sketch', payload.objects[0])
      Vue.set(state, 'meta', payload.meta)
    },
    SET_COUNT (state, payload) {
      Vue.set(state, 'count', payload)
    },
    RESET_STATE (state) {
      Object.assign(state, defaultState())
    }
  },
  actions: {
    updateSketch (context, sketchId) {
      ApiClient.getSketch(sketchId).then((response) => {
        context.commit('SET_SKETCH', response.data)
      }).catch((e) => {})

      // Count events for all timelines in the sketch
      ApiClient.countSketchEvents(sketchId).then((response) => {
        context.commit('SET_COUNT', response.data.meta.count)
      }).catch((e) => {})

    },
    resetState (context) {
      context.commit('RESET_STATE')
    }
  }
})



