/*
Copyright 2026 Google Inc. All rights reserved.

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

import { shallowMount, createLocalVue } from '@vue/test-utils'
import Vue from 'vue'
import Vuetify from 'vuetify'
import Vuex from 'vuex'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Sketch from './Sketch.vue'
import ApiClient from '../utils/RestApiClient.js'

const localVue = createLocalVue()
localVue.use(Vuex)
Vue.use(Vuetify)
Vue.filter('initialLetter', (val) => (val ? val[0] : ''))
Vue.filter('formatSeconds', (val) => val)

function flushPromises() {
  return new Promise((resolve) => setTimeout(resolve, 0))
}

describe('Sketch.vue archive permissions', () => {
  let vuetify
  let actions

  beforeEach(() => {
    vuetify = new Vuetify()
    actions = {
      updateUserSettings: vi.fn(() => Promise.resolve()),
      updateSketch: vi.fn(() => Promise.resolve()),
      updateSearchHistory: vi.fn(() => Promise.resolve()),
      updateScenarioTemplates: vi.fn(() => Promise.resolve()),
      updateSavedGraphs: vi.fn(() => Promise.resolve()),
      updateGraphPlugins: vi.fn(() => Promise.resolve()),
      updateContextLinks: vi.fn(() => Promise.resolve()),
      updateAnalyzerList: vi.fn(() => Promise.resolve()),
      updateSystemSettings: vi.fn(() => Promise.resolve()),
    }
  })

  function mountSketch({ status = 'archived', permissions = {} } = {}) {
    const store = new Vuex.Store({
      state: {
        sketch: {
          id: 42,
          name: 'Test Sketch',
          status: [{ id: 1, status }],
          timelines: [],
          active_timelines: [],
        },
        meta: {
          permissions,
          collaborators: { users: [], groups: [] },
          views: [],
          stories: [],
        },
        settings: { showLeftPanel: false },
        currentUser: 'test2',
        systemSettings: {},
        sketchAccessDenied: false,
        scenarios: [],
        activeContext: { question: null },
        enabledTimelines: [],
      },
      actions,
    })

    return shallowMount(Sketch, {
      localVue,
      vuetify,
      store,
      propsData: { sketchId: '42' },
      mocks: {
        $route: { name: 'Overview', params: { sketchId: '42' } },
        $router: { push: vi.fn() },
      },
      stubs: ['router-view', 'router-link'],
    })
  }

  it('shows Bring it back and Archive sketch for collaborators with write access', async () => {
    const wrapper = mountSketch({
      status: 'archived',
      permissions: { read: true, write: true, delete: false, admin: false },
    })
    await flushPromises()

    expect(wrapper.vm.canArchive).toBe(true)
    expect(wrapper.text()).toContain('Bring it back')
    expect(wrapper.text()).not.toContain(
      'Only users with write access or administrators can unarchive this sketch.'
    )
    expect(wrapper.text()).toContain('Archive sketch')
  })

  it('shows Bring it back for administrators without explicit write ACL', async () => {
    const wrapper = mountSketch({
      status: 'archived',
      permissions: { read: false, write: false, delete: false, admin: true },
    })
    await flushPromises()

    expect(wrapper.vm.canArchive).toBe(true)
    expect(wrapper.text()).toContain('Bring it back')
  })

  it('hides Bring it back and Archive sketch for read-only collaborators', async () => {
    const wrapper = mountSketch({
      status: 'archived',
      permissions: { read: true, write: false, delete: false, admin: false },
    })
    await flushPromises()

    expect(wrapper.vm.canArchive).toBe(false)
    expect(wrapper.text()).not.toContain('Bring it back')
    expect(wrapper.text()).toContain(
      'Only users with write access or administrators can unarchive this sketch.'
    )
    expect(wrapper.text()).not.toContain('Archive sketch')
  })

  it('resets loadingSketch when archive or unarchive API calls fail', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const unarchiveSpy = vi
      .spyOn(ApiClient, 'unArchiveSketch')
      .mockRejectedValue(new Error('403 Forbidden'))
    const archiveSpy = vi
      .spyOn(ApiClient, 'archiveSketch')
      .mockRejectedValue(new Error('403 Forbidden'))

    const wrapper = mountSketch({
      status: 'archived',
      permissions: { read: true, write: true, delete: false, admin: false },
    })
    await flushPromises()

    wrapper.vm.unArchiveSketch()
    expect(wrapper.vm.loadingSketch).toBe(true)
    await flushPromises()
    expect(wrapper.vm.loadingSketch).toBe(false)

    wrapper.vm.archiveSketch()
    expect(wrapper.vm.loadingSketch).toBe(true)
    await flushPromises()
    expect(wrapper.vm.loadingSketch).toBe(false)

    unarchiveSpy.mockRestore()
    archiveSpy.mockRestore()
    consoleSpy.mockRestore()
  })
})
