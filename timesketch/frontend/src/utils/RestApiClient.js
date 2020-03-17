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
import { ToastProgrammatic as Toast } from 'buefy'
import { SnackbarProgrammatic as Snackbar } from 'buefy'

const RestApiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    common: {
      'X-CSRFToken': document.getElementsByTagName('meta')[0]['content']
    }
  }
})

// Show message on errors.
RestApiClient.interceptors.response.use(function (response) {
  return response;
}, function (error) {
  if (error.response.data.message === 'The CSRF token has expired') {
    Snackbar.open({
      message: error.response.data.message,
      type: 'is-white',
      position: 'is-top',
      actionText: 'Refresh',
      indefinite: true,
      onAction: () => {
        location.reload()
      }}
    )
  } else {
    Toast.open(error.response.data.message)
  }
  return Promise.reject(error);
});

export default {
  // Sketch
  getSketchList () {
    return RestApiClient.get('/sketches/')
  },
  getSketch (sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/')
  },
  createSketch (formData) {
    return RestApiClient.post('/sketches/', formData)
  },
  deleteSketch (sketchId) {
    return RestApiClient.delete('/sketches/' + sketchId + '/')
  },
  getSketchTimelines (sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/timelines/')
  },
  getSketchTimeline (sketchId, timelineId) {
    return RestApiClient.get('/sketches/' + sketchId + '/timelines/' + timelineId + '/')
  },
  getSketchTimelineAnalysis (sketchId, timelineId) {
    return RestApiClient.get('/sketches/' + sketchId + '/timelines/' + timelineId + '/analysis/')
  },
  // Add or remove timeline to sketch
  createSketchTimeline (sketchId, searchIndexId) {
    let formData = {
      timeline: searchIndexId
    }
    return RestApiClient.post('/sketches/' + sketchId + /timelines/, formData)
  },
  saveSketchTimeline (sketchId, timelineId, name, description, color) {
    let formData = {
      name: name,
      description: description,
      color: color
    }
    return RestApiClient.post('/sketches/' + sketchId + /timelines/ + timelineId + '/', formData)
  },
  saveSketchSummary (sketchId, name, description) {
    let formData = {
      name: name,
      description: description
    }
    return RestApiClient.post('/sketches/' + sketchId + '/', formData)
  },
  deleteSketchTimeline (sketchId, timelineId) {
    return RestApiClient.delete('/sketches/' + sketchId + /timelines/ + timelineId + '/')
  },
  // Searchindices
  getSearchIndexList () {
    return RestApiClient.get('/searchindices/')
  },
  // Get details about an event
  getEvent (sketchId, searchindexId, eventId) {
    let params = {
      params: {
        searchindex_id: searchindexId,
        event_id: eventId
      }
    }
    return RestApiClient.get('/sketches/' + sketchId + '/event/', params)
  },
  saveEventAnnotation (sketchId, annotationType, annotation, events) {
    let formData = {
      annotation: annotation,
      annotation_type: annotationType,
      events: events,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/event/annotate/', formData)
  },
  // Stories
  getStoryList (sketchId) {
    return RestApiClient.get('sketches/' + sketchId + '/stories/')
  },
  getStory (sketchId, storyId) {
    return RestApiClient.get('/sketches/' + sketchId + '/stories/' + storyId + '/')
  },
  createStory (title, content, sketchId) {
    let formData = {
      title: title,
      content: content
    }
    return RestApiClient.post('/sketches/' + sketchId + /stories/, formData)
  },
  updateStory (title, content, sketchId, storyId) {
    let formData = {
      title: title,
      content: content
    }
    return RestApiClient.post('/sketches/' + sketchId + /stories/ + storyId + '/', formData)
  },
  // Saved views
  getView (sketchId, viewId) {
    return RestApiClient.get('/sketches/' + sketchId + '/views/' + viewId + '/')
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
  deleteView (sketchId, viewId) {
    return RestApiClient.delete('/sketches/' + sketchId + '/views/' + viewId + '/')
  },
  // Search
  search (sketchId, formData) {
    return RestApiClient.post('/sketches/' + sketchId + '/explore/', formData)
  },
  runAggregator (sketchId, formData) {
    return RestApiClient.post('/sketches/' + sketchId + '/aggregation/explore/', formData)
  },
  saveAggregation (sketchId, aggregation, formData) {
    let form_data = {
      'name': aggregation.display_name,
      'description': aggregation.description,
      'agg_type': aggregation.name,
      'chart_type': formData['supported_charts'],
      'parameters': formData
    }
    return RestApiClient.post('/sketches/' + sketchId + '/aggregation/', form_data)
    console.log(aggregation)
    console.log(form_data)
    console.log(formData)
  },
  // Misc resources
  countSketchEvents (sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/count/')
  },
  uploadTimeline (formData, config) {
    return RestApiClient.post('/upload/', formData, config)
  },
  getSessions (sketchId, timelineIndex) {
    return RestApiClient.get('/sketches/' + sketchId + '/explore/sessions/' + timelineIndex + '/')
  },
  getUsers () {
    return RestApiClient.get('/users/')
  },
  getGroups () {
    return RestApiClient.get('/groups/')
  },
  editCollaborators (sketchId, isPublic, usersToAdd, groupsToAdd, usersToRemove, groupsToRemove) {
    let formData = {
      public: isPublic,
      users: usersToAdd,
      groups: groupsToAdd,
      remove_users: usersToRemove,
      remove_groups: groupsToRemove
    }
    return RestApiClient.post('/sketches/' + sketchId + /collaborators/, formData)
  },
  runAnalyzers (sketchId, timelineId, analyzers) {
    let formData = {
      timeline_id: timelineId,
      analyzer_names: analyzers
    }
    return RestApiClient.post('/sketches/' + sketchId + /analyzer/, formData)
  },
  getAnalyzerSession (sketchId, sessionId) {
    return RestApiClient.get('/sketches/' + sketchId + '/analyzer/sessions/' + sessionId + '/')
  }
}
