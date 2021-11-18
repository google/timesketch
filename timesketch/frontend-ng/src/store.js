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

const defaultState = currentUser => {
  return {
    sketch: {},
    meta: {},
    searchHistory: {},
    tags: [],
    dataTypes: [],
    count: 0,
    currentSearchNode: null,
    currentUser: currentUser,
  }
}

// Initial state
const state = defaultState()

export default new Vuex.Store({
  state,
  mutations: {
    SET_SKETCH(state, payload) {
      Vue.set(state, 'sketch', payload.objects[0])
      Vue.set(state, 'meta', payload.meta)
    },
    SET_SEARCH_HISTORY(state, payload) {
      Vue.set(state, 'searchHistory', payload.objects)
    },
    SET_TIMELINE_TAGS(state, payload) {
      let buckets = payload.objects[0]['field_bucket']['buckets']
      Vue.set(state, 'tags', buckets)
    },
    SET_DATA_TYPES(state, payload) {
      let buckets = payload.objects[0]['field_bucket']['buckets']
      Vue.set(state, 'dataTypes', buckets)
    },
    SET_COUNT(state, payload) {
      Vue.set(state, 'count', payload)
    },
    SET_SEARCH_NODE(state, payload) {
      Vue.set(state, 'currentSearchNode', payload)
    },
    SET_SIGMA_LIST(state, payload) {
      Vue.set(state, 'sigmaRuleList', payload['objects'])
      Vue.set(state, 'sigmaRuleList_count', payload['meta']['rules_count'])
    },
    RESET_STATE(state, payload) {
      ApiClient.getLoggedInUser().then(response => {
        let currentUser = response.data.objects[0].username
        Object.assign(state, defaultState(currentUser))
      })
    },
  },
  actions: {
    updateSketch(context, sketchId) {
      return ApiClient.getSketch(sketchId)
        .then(response => {
          // console.log(response.data.objects[0].active_timelines[0].color)
          context.commit('SET_SKETCH', response.data)
          context.dispatch('updateTimelineTags', sketchId)
          context.dispatch('updateDataTypes', sketchId)
        })
        .catch(e => {})
    },
    updateCount(context, sketchId) {
      // Count events for all timelines in the sketch
      return ApiClient.countSketchEvents(sketchId)
        .then(response => {
          context.commit('SET_COUNT', response.data.meta.count)
        })
        .catch(e => {})
    },
    resetState(context) {
      context.commit('RESET_STATE')
    },
    updateSearchNode(context, nodeId) {
      context.commit('SET_SEARCH_NODE', nodeId)
    },
    updateSearchHistory(context, sketchId) {
      if (!sketchId) {
        sketchId = context.state.sketch.id
      }
      return ApiClient.getSearchHistory(sketchId)
        .then(response => {
          context.commit('SET_SEARCH_HISTORY', response.data)
        })
        .catch(e => {})
    },
    updateTimelineTags(context, sketchId) {
      if (!context.state.sketch.active_timelines.length) {
        return
      }
      let formData = {
        aggregator_name: 'field_bucket',
        aggregator_parameters: {
          field: 'tag',
        },
      }
      return ApiClient.runAggregator(sketchId, formData)
        .then(response => {
          context.commit('SET_TIMELINE_TAGS', response.data)
        })
        .catch(e => {})
    },
    updateDataTypes(context, sketchId) {
      if (!context.state.sketch.active_timelines.length) {
        return
      }
      let formData = {
        aggregator_name: 'field_bucket',
        aggregator_parameters: {
          field: 'data_type',
        },
      }
      return ApiClient.runAggregator(sketchId, formData)
        .then(response => {
          context.commit('SET_DATA_TYPES', response.data)
        })
        .catch(e => {})
    },
    updateSigmaList(context) {
      ApiClient.getSigmaList()
      .then(response => {
        context.commit('SET_SIGMA_LIST', response.data)
      }).catch(e => {})
    },
  },
})
