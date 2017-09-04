/*
Copyright 2015 Google Inc. All rights reserved.

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
import angular from 'angularjs-for-webpack'

export const timesketchApiImplementation = function ($http) {
    const API_BASE_URL = '/api/v1'
    const SKETCH_BASE_URL = API_BASE_URL + '/sketches/'

    this.getSketch = function (sketch_id) {
        /**
         * Get a Timesketch view.
         * @param sketch_id - The id for the sketch.
         * @param view_id - The id for the view.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/'
        return $http.get(resource_url)
    }

    this.getTimelines = function (sketch_id) {
        /**
         * Get all timelines for sketch.
         * @param sketch_id - The id for the sketch.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/timelines/'
        return $http.get(resource_url)
    }

    this.deleteTimeline = function (sketch_id, timeline_id) {
        /**
         * Delete a Timesketch view.
         * @param sketch_id - The id for the sketch.
         * @param timeline_id - The id of the timeline.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/timelines/' + timeline_id + '/'
        return $http.delete(resource_url)
    }

    this.getViews = function (sketch_id) {
        /**
         * Get all saved views for sketch.
         * @param sketch_id - The id for the sketch.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/views/'
        return $http.get(resource_url)
    }

    this.getSearchTemplates = function () {
        /**
         * Get list of all search templates.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = API_BASE_URL + '/searchtemplate/'
        return $http.get(resource_url)
    }

    this.getSearchTemplate = function (searchtemplate_id) {
        /**
         * Get a specific search templates.
         * @param searchtemplate_id - The id for the searchtemplate.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = API_BASE_URL + '/searchtemplate/' + searchtemplate_id + '/'
        return $http.get(resource_url)
    }

    this.getView = function (sketch_id, view_id) {
        /**
         * Get a Timesketch view.
         * @param sketch_id - The id for the sketch.
         * @param view_id - The id for the view.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/views/' + view_id + '/'
        return $http.get(resource_url)
    }

    this.deleteView = function (sketch_id, view_id) {
        /**
         * Delete a Timesketch view.
         * @param sketch_id - The id for the sketch.
         * @param view_id - The id for the view.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/views/' + view_id + '/'
        return $http.delete(resource_url)
    }

    this.saveView = function (sketch_id, name, new_searchtemplate, query, filter, queryDsl) {
        /**
         * Save a Timesketch view.
         * @param sketch_id - The id for the sketch.
         * @param name - A name for the view.
         * @param new_searchtemplate - Boolean indicating if a search template should be created.
         * @param query - A query string.
         * @param filter - A JSON string with filters and a list of indices.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/views/'
        const params = {
            name: name,
            new_searchtemplate: new_searchtemplate,
            query: query,
            filter: filter,
            dsl: queryDsl,
        }
        return $http.post(resource_url, params)
    }

    this.saveViewFromSearchTemplate = function (sketch_id, searchtemplate_id) {
        /**
         * Save a Timesketch view.
         * @param sketch_id - The id for the sketch.
         * @param searchtemplate_id - The id for the search template to create from.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/views/'
        const params = {
            from_searchtemplate_id: searchtemplate_id,
        }
        return $http.post(resource_url, params)
    }

    this.updateView = function (sketch_id, view_id, name, query, filter, queryDsl) {
        /**
         * Save a Timesketch view.
         * @param sketch_id - The id for the sketch.
         * @param view_id - A name for the view.
         * @param name - A name for the view.
         * @param query - A query string.
         * @param filter - A JSON string with filters and a list of indices.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/views/' + view_id + '/'
        const params = {
            name: name,
            query: query,
            filter: filter,
            dsl: queryDsl,
        }
        return $http.post(resource_url, params)
    }

    this.createStory = function (sketch_id) {
        /**
         * Creates a new story.
         * @param sketch_id - The id for the sketch.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/stories/'
        const params = {
            sketch_id: sketch_id,
        }
        return $http.post(resource_url, params)
    }

    this.updateStory = function (sketch_id, story_id, title, content) {
        /**
         * Updates a story.
         * @param sketch_id - The id for the sketch.
         * @param story_id - The id for the story.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/stories/' + story_id + '/'
        const params = {
            sketch_id: sketch_id,
            story_id: story_id,
            title: title,
            content: content,
        }
        return $http.post(resource_url, params)
    }

    this.getStories = function (sketch_id) {
        /**
         * Get stories for sketch.
         * @param sketch_id - The id for the sketch.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/stories/'
        const params = {
            sketch_id: sketch_id,
        }
        return $http.get(resource_url, params)
    }

    this.getStory = function (sketch_id, story_id) {
        /**
         * Get story for sketch.
         * @param sketch_id - The id for the sketch.
         * @param story_id - The id for the story.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/stories/' + story_id + '/'
        const params = {
            sketch_id: sketch_id,
            story_id: story_id,
        }
        return $http.get(resource_url, params)
    }

    this.getEvent = function (sketch_id, searchindex_id, event_id) {
        /**
         * Get a Timesketch event.
         * @param sketch_id - The id for the sketch.
         * @param searchindex_id - The id for the search index.
         * @param event_id - The id for the event.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/event/'
        const params = {
            params: {
                searchindex_id: searchindex_id,
                event_id: event_id,
            },
        }
        return $http.get(resource_url, params)
    }

    this.saveEventAnnotation = function (sketch_id, annotation_type, annotation, events) {
        /**
         * Save a Timesketch event annotation.
         * @param sketch_id - The id for the sketch.
         * @param type - The type of the annotation, e.g. comment or tag.
         * @param annotation - The content for the annotation.
         * @param events - List of events.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/event/annotate/'
        const params = {
            annotation: annotation,
            annotation_type: annotation_type,
            events: events,
        }
        return $http.post(resource_url, params)
    }

    this.getCurrentQuery = function (sketch_id, query, filter, queryDsl) {
        /**
         * Execute query and filter on the datastore.
         * @param sketch_id - The id for the sketch.
         * @param query - A query string.
         * @param filter - A JSON string with filters and a list of indices.
         * @param queryDsl - A JSON string with Elasticsearch DLS.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/explore/query/'
        const params = {
            query: query,
            filter: filter,
            dsl: queryDsl,
        }
        return $http.post(resource_url, params)
    }

    this.countEvents = function (sketch_id) {
        /**
         * Count number of events in sketch.
         * @param sketch_id - The id for the sketch.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/count/'
        return $http.get(resource_url)
    }

    this.search = function (sketch_id, query, filter, queryDsl) {
        /**
         * Execute query and filter on the datastore.
         * @param sketch_id - The id for the sketch.
         * @param query - A query string.
         * @param filter - A JSON string with filters and a list of indices.
         * @param queryDsl - A JSON string with Elasticsearch DLS.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/explore/'
        const params = {
            query: query,
            filter: filter,
            dsl: queryDsl,
        }
        return $http.post(resource_url, params)
    }

    this.aggregation = function (sketch_id, query, filter, queryDsl, aggtype) {
        /**
         * Execute query and filter on the datastore.
         * @param sketch_id - The id for the sketch.
         * @param query - A query string.
         * @param filter - A JSON string with filters and a list of indices.
         * @param queryDsl - A JSON string with Elasticsearch DLS.
         * @param aggtype - Type of aggregation.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = SKETCH_BASE_URL + sketch_id + '/aggregation/'
        const params = {
            query: query,
            filter: filter,
            dsl: queryDsl,
            aggtype: aggtype,
        }
        return $http.post(resource_url, params)
    }

    this.uploadFile = function (file, name, sketchId) {
        /**
         * Handles the upload form and send a POST request to the server.
         * @param file - File object.
         * @param name - Name if the timeline to be created.
         * @param sketchId - (optional) Sketch id to add the timeline to.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = '/api/v1/upload/'
        // Default Content-Type in angular for GET/POST is application/json
        // so we nee to change this. By setting this to undefined we let the
        // browser set the Content-Type to multipart/form-data and also set
        // the correct boundary parameters.
        const config = {
            transformRequest: angular.identity,
            headers: {
                'Content-Type': undefined,
            },
        }
        const formData = new FormData()
        formData.append('file', file)
        formData.append('name', name)
        formData.append('sketch_id', sketchId)
        return $http.post(resource_url, formData, config)
    }

    this.getTasks = function () {
        /**
         * Get Celery tasks status.
         * @returns A $http promise with two methods, success and error.
         */
        const resource_url = '/api/v1/tasks/'
        return $http.get(resource_url)
    }

}
