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
    searchInProgress: false,
    currentQueryString: '',
    currentQueryFilter: {
      'from': 0,
      'time_start': null,
      'time_end': null,
      'terminate_after': 40,
      'size': 40,
      'indices': ['_all'],
      'order': 'asc',
      'chips': [
        {'field': 'domain', 'value': 'grendale.xyz', 'type': 'term', 'operator': 'must_not'},
        // {'field': 'ts_label', 'value': '__ts_star', 'type': 'label', 'operator': 'must'},
        // {'field': '', 'value': 'testus', 'type': 'label', 'operator': ''},
        {'field': '', 'value': '2015-08-22,2015-08-22', 'type': 'datetime_range', 'operator': 'must'},
        {'field': '', 'value': '2015-08-24,2015-08-24', 'type': 'datetime_range', 'operator': 'must'},
        // {'field': '', 'value': '2019-01-01,2019-01-02', 'type': 'datetime_range', 'operator': 'must'},
      ]
    }
  }
}

/*
{
  'field': '',
  'value': '',
  'operator': ''
}

 */

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
    search (state, sketchId) {
      Vue.set(state, 'searchInProgress', true)
      let formData = {
        'query': this.state.currentQueryString,
        'filter': this.state.currentQueryFilter
      }
      ApiClient.search(sketchId, formData).then((response) => {
        Vue.set(state, 'eventList', response.data)
        Vue.set(state, 'searchInProgress', false)
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
    updateSearchInProgress (state, isSearching) {
      Vue.set(state, 'searchInProgress', isSearching)
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
