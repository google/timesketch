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
import EventBus from '../event-bus.js'

const RestApiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    common: {
      'X-CSRFToken': document.getElementsByTagName('meta')[0]['content'],
    },
  },
})

const RestApiBlobClient = axios.create({
  baseURL: '/api/v1',
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
    if (error.response.status === 500) {
      EventBus.$emit(
        'errorSnackBar',
        'Server side error. Please contact your server administrator for troubleshooting.'
      )
    } else {
      EventBus.$emit('errorSnackBar', error.response.data.message)
    }
    return Promise.reject(error)
  }
)

export default {
  // Sketch
  getSketchList(scope, page, perPage, searchQuery) {
    let params = {
      params: {
        scope: scope,
        page: page,
        per_page: perPage,
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
    return RestApiClient.post('/sketches/' + sketchId + '/timelines/' + timelineId + '/', formData)
  },
  saveSketchSummary(sketchId, name, description) {
    let formData = {
      name: name,
      description: description,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/', formData)
  },
  deleteSketchTimeline(sketchId, timelineId) {
    return RestApiClient.delete('/sketches/' + sketchId + '/timelines/' + timelineId + '/')
  },
  createEvent(sketchId, datetime, message, timestampDesc, attributes, config) {
    let formData = {
      date_string: datetime,
      message: message,
      timestamp_desc: timestampDesc,
      attributes: attributes,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/event/create/', formData, config)
  },
  getEvent(sketchId, searchindexId, eventId) {
    let params = {
      params: {
        searchindex_id: searchindexId,
        event_id: eventId,
      },
    }
    return RestApiClient.get('/sketches/' + sketchId + '/event/', params)
  },
  countSketchEvents(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/count/')
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
  tagEvents(sketchId, events, tags) {
    let formData = {
      tag_string: JSON.stringify(tags),
      events: events,
      verbose: false,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/event/tagging/', formData)
  },
  untagEvents(sketchId, events, tags) {
    let formData = {
      tags_to_remove: tags,
      events: events,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/event/untag/', formData)
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
    return RestApiClient.post('/sketches/' + sketchId + '/stories/', formData)
  },
  updateStory(title, content, sketchId, storyId) {
    let formData = {
      title: title,
      content: content,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/stories/' + storyId + '/', formData)
  },
  deleteStory(sketchId, storyId) {
    return RestApiClient.delete('/sketches/' + sketchId + '/stories/' + storyId + '/')
  },
  getView(sketchId, viewId) {
    return RestApiClient.get('/sketches/' + sketchId + '/views/' + viewId + '/')
  },
  // Saved searches
  createView(sketchId, viewName, queryString, queryFilter) {
    let formData = {
      name: viewName,
      query: queryString,
      filter: queryFilter,
      dsl: '',
    }
    return RestApiClient.post('/sketches/' + sketchId + '/views/', formData)
  },
  updateView(sketchId, viewId, queryString, queryFilter) {
    let formData = {
      query: queryString,
      filter: queryFilter,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/views/' + viewId + '/', formData)
  },
  deleteView(sketchId, viewId) {
    return RestApiClient.delete('/sketches/' + sketchId + '/views/' + viewId + '/')
  },
  // Search templates
  getSearchTemplates() {
    return RestApiClient.get('/searchtemplates/')
  },
  parseSearchTemplate(searchTemplateId, formData) {
    return RestApiClient.post('/searchtemplates/' + searchTemplateId + '/parse/', formData)
  },
  // Search
  search(sketchId, formData) {
    return RestApiClient.post('/sketches/' + sketchId + '/explore/', formData)
  },
  exportSearchResult(sketchId, formData) {
    return RestApiBlobClient.post('/sketches/' + sketchId + '/explore/', formData)
  },
  getSearchHistory(sketchId, limit = null, question = null) {
    let params = { params: {} }
    if (limit) {
      params.params.limit = limit
    }
    if (question) {
      params.params.question = question
    }
    return RestApiClient.get('/sketches/' + sketchId + '/searchhistory/', params)
  },
  getSearchHistoryTree(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/searchhistorytree/')
  },
  // Aggregations
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
  // Sharing and authorization
  getUsers() {
    return RestApiClient.get('/users/')
  },
  getGroups() {
    return RestApiClient.get('/groups/')
  },
  grantSketchAccess(sketchId, usersToAdd, groupsToAdd) {
    let formData = {
      users: usersToAdd,
      groups: groupsToAdd,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/collaborators/', formData)
  },
  revokeSketchAccess(sketchId, usersToRemove, groupsToRemove) {
    let formData = {
      remove_users: usersToRemove,
      remove_groups: groupsToRemove,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/collaborators/', formData)
  },
  setSketchPublicAccess(sketchId, isPublic) {
    let formData = {
      public: isPublic,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/collaborators/', formData)
  },
  // Analyzers
  getAnalyzers(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/analyzer/')
  },
  runAnalyzers(sketchId, timelineIds, analyzers, forceRun = false) {
    let formData = {
      timeline_ids: timelineIds,
      analyzer_names: analyzers,
      analyzer_force_run: forceRun,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/analyzer/', formData)
  },
  getAnalyzerSession(sketchId, sessionId) {
    return RestApiClient.get('/sketches/' + sketchId + '/analyzer/sessions/' + sessionId + '/')
  },
  getActiveAnalyzerSessions(sketchId) {
    let params = {
      params: {
        include_details: 'true',
      },
    }
    return RestApiClient.get('/sketches/' + sketchId + '/analyzer/sessions/active/', params)
  },
  // Graphs
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
    return RestApiClient.post('/sketches/' + sketchId + '/graph/', formData)
  },
  getGraphPluginList() {
    return RestApiClient.get('/graphs/')
  },
  saveGraph(sketchId, name, elements) {
    let formData = {
      name: name,
      elements: elements,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/graphs/', formData)
  },
  getSavedGraphList(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/graphs/')
  },
  getSavedGraph(sketchId, graphId) {
    let params = {
      params: {
        format: 'cytoscape',
      },
    }
    return RestApiClient.get('/sketches/' + sketchId + '/graphs/' + graphId + '/', params)
  },
  // Sigma
  getSigmaRuleList() {
    return RestApiClient.get('/sigmarules/')
  },
  getSigmaRuleResource(ruleUuid) {
    return RestApiClient.get('/sigmarules/' + ruleUuid + '/')
  },
  getSigmaRuleByText(ruleYaml) {
    let formData = {
      content: ruleYaml,
    }
    return RestApiClient.post('/sigmarules/text/', formData)
  },
  deleteSigmaRule(ruleUuid) {
    return RestApiClient.delete('/sigmarules/' + ruleUuid + '/')
  },
  createSigmaRule(ruleYaml) {
    let formData = {
      rule_yaml: ruleYaml,
    }
    return RestApiClient.post('/sigmarules/', formData)
  },
  updateSigmaRule(id, ruleYaml) {
    let formData = {
      id: id,
      rule_yaml: ruleYaml,
    }
    return RestApiClient.put('/sigmarules/' + id + '/', formData)
  },
  // Scenarios
  getScenarioTemplates() {
    return RestApiClient.get('/scenarios/')
  },
  getSketchScenarios(sketchId, status = null) {
    let params = {}
    if (status) {
      params.params = {
        status: status,
      }
    }
    return RestApiClient.get('/sketches/' + sketchId + '/scenarios/', params)
  },
  addScenario(sketchId, scenarioId, displayName) {
    let formData = { scenario_id: scenarioId, display_name: displayName }
    return RestApiClient.post('/sketches/' + sketchId + '/scenarios/', formData)
  },
  renameScenario(sketchId, scenarioId, scenarioName) {
    let formData = { scenario_name: scenarioName }
    return RestApiClient.post('/sketches/' + sketchId + '/scenarios/' + scenarioId + '/', formData)
  },
  setScenarioStatus(sketchId, scenarioId, status) {
    let formData = { status: status }
    return RestApiClient.post('/sketches/' + sketchId + '/scenarios/' + scenarioId + '/status/', formData)
  },
  getFacets(sketchId, scenarioId) {
    return RestApiClient.get('/sketches/' + sketchId + '/scenarios/' + scenarioId + '/facets/')
  },
  getQuestionTemplates() {
    return RestApiClient.get('/questions/')
  },
  getOrphanQuestions(sketchId) {
    return RestApiClient.get('/sketches/' + sketchId + '/questions/')
  },
  getScenarioQuestions(sketchId, scenarioId) {
    return RestApiClient.get('/sketches/' + sketchId + '/scenarios/' + scenarioId + '/questions/')
  },
  getFacetQuestions(sketchId, scenarioId, facetId) {
    return RestApiClient.get(
      '/sketches/' + sketchId + '/scenarios/' + scenarioId + '/facets/' + facetId + '/questions/'
    )
  },
  getQuestion(sketchId, questionId) {
    return RestApiClient.get('/sketches/' + sketchId + '/questions/' + questionId + '/')
  },
  createQuestion(sketchId, scenarioId, facetId, questionText, templateId) {
    let formData = {
      scenario_id: scenarioId,
      facet_id: facetId,
      question_text: questionText,
      template_id: templateId,
    }
    return RestApiClient.post('/sketches/' + sketchId + '/questions/', formData)
  },
  createQuestionConclusion(sketchId, questionId, conclusionText) {
    let formData = { conclusionText: conclusionText }
    return RestApiClient.post('/sketches/' + sketchId + '/questions/' + questionId + '/conclusions/', formData)
  },
  editQuestionConclusion(sketchId, questionId, conclusionId, conclusionText) {
    let formData = { conclusionText: conclusionText }
    return RestApiClient.put(
      '/sketches/' + sketchId + '/questions/' + questionId + '/conclusions/' + conclusionId + '/',
      formData
    )
  },
  deleteQuestionConclusion(sketchId, questionId, conclusionId) {
    return RestApiClient.delete(
      '/sketches/' + sketchId + '/questions/' + questionId + '/conclusions/' + conclusionId + '/'
    )
  },
  // Misc resources
  getTagMetadata() {
    return RestApiClient.get('/intelligence/tagmetadata/')
  },
  uploadTimeline(formData, config) {
    return RestApiClient.post('/upload/', formData, config)
  },
  getSessions(sketchId, timelineIndex) {
    return RestApiClient.get('/sketches/' + sketchId + '/explore/sessions/' + timelineIndex + '/')
  },
  getLoggedInUser() {
    return RestApiClient.get('/users/me/')
  },
  getContextLinkConfig() {
    return RestApiClient.get('/contextlinks/')
  },
  getUnfurlGraph(url) {
    let formData = {
      url: url,
    }
    return RestApiClient.post('/unfurl/', formData)
  },
  getUserSettings() {
    return RestApiClient.get('/users/me/settings/')
  },
  saveUserSettings(settings) {
    let formData = { settings: settings }
    return RestApiClient.post('/users/me/settings/', formData)
  },
}
