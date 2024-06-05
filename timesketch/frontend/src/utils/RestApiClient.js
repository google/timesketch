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
import { SnackbarProgrammatic as Snackbar } from 'buefy'

const RestApiClient = axios.create({
  baseURL: process.env.NODE_ENV === 'development' ? '/api/v1' : '/legacy/api/v1',
  headers: {
    common: {
      'X-CSRFToken': document.getElementsByTagName('meta')[0]['content'],
    },
  },
})

const RestApiBlobClient = axios.create({
  baseURL: process.env.NODE_ENV === 'development' ? '/api/v1' : '/legacy/api/v1',
  responseType: 'blob',
  headers: {
    common: {
      'X-CSRFToken': document.getElementsByTagName('meta')[0]['content'],
    },
  },
})

// Show message on errors.
RestApiClient.interceptors.response.use(
  function (response) {
    return response
  },
  function (error) {
    if (error.response.data.message === 'The CSRF token has expired.') {
      Snackbar.open({
        message: error.response.data.message,
        type: 'is-white',
        position: 'is-top',
        actionText: 'Refresh',
        indefinite: true,
        onAction: () => {
          location.reload()
        },
      })
    } else {
      console.error(error.response.data)
      Snackbar.open({
        message: `Error: "${error.message}" (see console for details)`,
        type: 'is-danger',
        position: 'is-top',
        actionText: 'Close',
        duration: 7000,
      })
    }
    return Promise.reject(error)
  }
)

export default {
  // Sketch
  getSketchList(scope, page, searchQuery) {
    let params = {
      params: {
        scope: scope,
        page: page,
        search_query: searchQuery,
      },
    }
    return RestApiClient.get('/sketches/', params)
  },
  getSketch(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/')
  },
  createSketch(formData) {
    return RestApiClient.post('/sketches/', formData)
  },
  deleteSketch(sketchId) {
    return RestApiClient.delete('/sketches/' + sketchId + '/')
  },
  archiveSketch(sketchId) {
    let formData = {
      action: 'archive',
    }
    return RestApiClient.post('/sketches/' + sketchId + '/archive/', formData)
  },
  unArchiveSketch(sketchId) {
    let formData = {
      action: 'unarchive',
    }
    return RestApiClient.post('/sketches/' + sketchId + '/archive/', formData)
  },
  exportSketch(sketchId) {
    let formData = {
      action: 'export',
    }
    return RestApiBlobClient.post('/sketches/' + sketchId + '/archive/', formData)
  },
  getSketchAttributes(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/attribute/')
  },
  addSketchAttribute(sketchId, name, value, ontology) {
    let attribute = {
      name: name,
      values: [value],
      ontology: ontology,
      action: 'post',
    }
    return RestApiClient.post('/sketches/' + sketchId + '/attribute/', attribute)
  },
  getSketchTimeline(sketchId, timelineId) {
    return RestApiClient.get('/sketches/' + sketchId + '/timelines/' + timelineId + '/')
  },
  getSketchTimelineAnalysis(sketchId, timelineId) {
    return RestApiClient.get('/sketches/' + sketchId + '/timelines/' + timelineId + '/analysis/')
  },
  saveSketchTimeline(sketchId, timelineId, name, description, color) {
    let formData = {
      name: name,
      description: description,
      color: color,
    }
    return RestApiClient.post('/sketches/' + sketchId + /timelines/ + timelineId + '/', formData)
  },
  saveSketchSummary(sketchId, name, description) {
    let formData = {
      name: name,
      description: description,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/', formData)
  },
  deleteSketchTimeline(sketchId, timelineId) {
    return RestApiClient.delete('/sketches/' + sketchId + /timelines/ + timelineId + '/')
  },
  // Get details about an event
  getEvent(sketchId, searchindexId, eventId) {
    let params = {
      params: {
        searchindex_id: searchindexId,
        event_id: eventId,
      },
    }
    return RestApiClient.get('/sketches/' + sketchId + '/event/', params)
  },
  saveEventAnnotation(sketchId, annotationType, annotation, events, currentSearchNode, remove = false) {
    let formData = {
      annotation: annotation,
      annotation_type: annotationType,
      events: events,
      current_search_node_id: currentSearchNode.id,
      remove: remove,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/event/annotate/', formData)
  },
  updateEventAnnotation(sketchId, annotationType, annotation, events, currentSearchNode) {
    let formData = {
      annotation: annotation,
      annotation_type: annotationType,
      events: events,
      current_search_node_id: currentSearchNode.id,
    }
    return RestApiClient.put('/sketches/' + sketchId + '/event/annotate/', formData)
  },
  deleteEventAnnotation(sketchId, annotationType, annotationId, event, currentSearchNode) {
    let params = {
      params: {
        annotation_id: annotationId,
        annotation_type: annotationType,
        event_id: event._id,
        searchindex_id: event._index,
        current_search_node_id: currentSearchNode.id,
      },
    }
    return RestApiClient.delete('/sketches/' + sketchId + '/event/annotate/', params)
  },
  // Stories
  getStoryList(sketchId) {
    return RestApiClient.get('sketches/' + sketchId + '/stories/')
  },
  getStory(sketchId, storyId) {
    return RestApiClient.get('/sketches/' + sketchId + '/stories/' + storyId + '/')
  },
  createStory(title, content, sketchId) {
    let formData = {
      title: title,
      content: content,
    }
    return RestApiClient.post('/sketches/' + sketchId + /stories/, formData)
  },
  updateStory(title, content, sketchId, storyId) {
    let formData = {
      title: title,
      content: content,
    }
    return RestApiClient.post('/sketches/' + sketchId + /stories/ + storyId + '/', formData)
  },
  deleteStory(sketchId, storyId) {
    return RestApiClient.delete('/sketches/' + sketchId + /stories/ + storyId + '/')
  },
  // Saved views
  getView(sketchId, viewId) {
    return RestApiClient.get('/sketches/' + sketchId + '/views/' + viewId + '/')
  },
  createView(sketchId, viewName, queryString, queryFilter) {
    let formData = {
      name: viewName,
      query: queryString,
      filter: queryFilter,
      dsl: '',
    }
    return RestApiClient.post('/sketches/' + sketchId + /views/, formData)
  },
  updateView(sketchId, viewId, queryString, queryFilter) {
    let formData = {
      query: queryString,
      filter: queryFilter,
    }
    return RestApiClient.post('/sketches/' + sketchId + /views/ + viewId + '/', formData)
  },
  deleteView(sketchId, viewId) {
    return RestApiClient.delete('/sketches/' + sketchId + '/views/' + viewId + '/')
  },
  // Search
  search(sketchId, formData) {
    return RestApiClient.post('/sketches/' + sketchId + '/explore/', formData)
  },
  exportSearchResult(sketchId, formData) {
    return RestApiBlobClient.post('/sketches/' + sketchId + '/explore/', formData)
  },
  getAggregations(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/aggregation/')
  },
  getAggregationGroups(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/aggregation/group/')
  },
  runAggregator(sketchId, formData) {
    return RestApiClient.post('/sketches/' + sketchId + '/aggregation/explore/', formData)
  },
  runAggregatorGroup(sketchId, groupId) {
    return RestApiClient.get('/sketches/' + sketchId + '/aggregation/group/' + groupId + '/')
  },
  saveAggregation(sketchId, aggregation, name, formData) {
    let newFormData = {
      name: name,
      description: aggregation.description,
      agg_type: aggregation.name,
      chart_type: formData['supported_charts'],
      parameters: formData,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/aggregation/', newFormData)
  },
  // Misc resources
  countSketchEvents(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/count/')
  },
  uploadTimeline(formData, config) {
    return RestApiClient.post('/upload/', formData, config)
  },
  getSessions(sketchId, timelineIndex) {
    return RestApiClient.get('/sketches/' + sketchId + '/explore/sessions/' + timelineIndex + '/')
  },
  getUsers() {
    return RestApiClient.get('/users/')
  },
  getGroups() {
    return RestApiClient.get('/groups/')
  },
  editCollaborators(sketchId, isPublic, usersToAdd, groupsToAdd, usersToRemove, groupsToRemove) {
    let formData = {
      public: isPublic,
      users: usersToAdd,
      groups: groupsToAdd,
      remove_users: usersToRemove,
      remove_groups: groupsToRemove,
    }
    return RestApiClient.post('/sketches/' + sketchId + /collaborators/, formData)
  },
  getAnalyzers(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/analyzer/')
  },
  runAnalyzers(sketchId, timelineIds, analyzers) {
    let formData = {
      timeline_ids: timelineIds,
      analyzer_names: analyzers,
    }
    return RestApiClient.post('/sketches/' + sketchId + /analyzer/, formData)
  },
  getAnalyzerSession(sketchId, sessionId) {
    return RestApiClient.get('/sketches/' + sketchId + '/analyzer/sessions/' + sessionId + '/')
  },
  getActiveAnalyzerSessions(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/analyzer/sessions/active/')
  },
  getLoggedInUser() {
    return RestApiClient.get('/users/me/')
  },
  generateGraphFromPlugin(sketchId, graphPlugin, currentIndices, timelineIds, refresh) {
    let formData = {
      plugin: graphPlugin,
      config: {
        filter: {
          indices: currentIndices,
          timelineIds: timelineIds,
        },
      },
      refresh: refresh,
    }
    if (timelineIds.length) {
      formData['timeline_ids'] = timelineIds
    }
    return RestApiClient.post('/sketches/' + sketchId + /graph/, formData)
  },
  getGraphPluginList() {
    return RestApiClient.get('/graphs/')
  },
  saveGraph(sketchId, name, elements) {
    let formData = {
      name: name,
      elements: elements,
    }
    return RestApiClient.post('/sketches/' + sketchId + /graphs/, formData)
  },
  getSavedGraphList(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + /graphs/)
  },
  getSavedGraph(sketchId, graphId) {
    let params = {
      params: {
        format: 'cytoscape',
      },
    }
    return RestApiClient.get('/sketches/' + sketchId + /graphs/ + graphId + '/', params)
  },
  getSearchHistory(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + /searchhistory/)
  },
  getSearchHistoryTree(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + /searchhistorytree/)
  },
  // SigmaRule (new rules file based)
  getSigmaRuleList() {
    return RestApiClient.get('/sigmarules/')
  },
  getSigmaRuleResource(ruleUuid) {
    return RestApiClient.get('/sigmarules/' + ruleUuid + '/')
  },
  getSigmaRuleByText(ruleText) {
    let formData = {
      content: ruleText,
    }
    return RestApiClient.post('/sigmarules/text/', formData)
  },
  deleteSigmaRule(ruleUuid) {
    return RestApiClient.delete('/sigmarules/' + ruleUuid + '/')
  },
  createSigmaRule(ruleText) {
    let formData = {
      rule_yaml: ruleText,
    }
    return RestApiClient.post('/sigmarules/', formData)
  },
  updateSigmaRule(id, ruleText) {
    let formData = {
      id: id,
      rule_yaml: ruleText,
    }
    return RestApiClient.put('/sigmarules/' + id + '/', formData)
  },
  getTagMetadata() {
    return RestApiClient.get('/intelligence/tagmetadata/')
  }
}
