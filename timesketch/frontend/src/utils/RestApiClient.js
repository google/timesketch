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
import axios from 'axios'

const RestApiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    common: {
      'X-CSRFToken': document.getElementsByTagName('meta')[0]['content']
    }
  }
})

export default {
  getSketchList () {
    return RestApiClient.get('/sketches/')
  },
  getSketch (sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/')
  },
  getEvent (sketchId, searchindexId, eventId) {
    let params = {
      params: {
        searchindex_id: searchindexId,
        event_id: eventId
      }
    }
    return RestApiClient.get('/sketches/' + sketchId + '/event/', params)
  },
  createSketch (formData) {
    return RestApiClient.post('/sketches/', formData)
  },
  getStoryList (sketchId) {
    return RestApiClient.get('sketches/' + sketchId + '/stories/')
  },
  createStory (title, content, sketchId) {
    let formData = {
      title: title,
      content: content
    }
    return RestApiClient.post('/sketches/' + sketchId + /stories/, formData)
  },
  createView (sketchId, viewName, queryString, queryFilter) {
    let formData = {
      name: viewName,
      query: queryString,
      filter: queryFilter,
      dsl: ''
    }
    return RestApiClient.post('/sketches/' + sketchId + /views/, formData)
  },
  updateStory (title, content, sketchId, storyId) {
    let formData = {
      title: title,
      content: content
    }
    return RestApiClient.post('/sketches/' + sketchId + /stories/ + storyId + '/', formData)
  },
  getView (sketchId, viewId) {
    return RestApiClient.get('/sketches/' + sketchId + '/views/' + viewId)
  },
  getStory (sketchId, storyId) {
    return RestApiClient.get('/sketches/' + sketchId + '/stories/' + storyId)
  },
  countSketchEvents (sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/count/')
  },
  search (id, formData) {
    return RestApiClient.post('/sketches/' + id + '/explore/', formData)
  },
  uploadTimeline (formData) {
    let config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
    return RestApiClient.post('/upload/', formData, config)
  }
}
