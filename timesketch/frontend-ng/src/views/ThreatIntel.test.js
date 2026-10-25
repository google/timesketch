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
import { mount, createLocalVue } from '@vue/test-utils'
import ThreatIntel from './ThreatIntel.vue'
import Vuetify from 'vuetify'
import Vuex from 'vuex'
import Vue from 'vue'
import { vi, expect, it, describe, beforeEach, afterEach } from 'vitest'
import ApiClient from '../utils/RestApiClient.js'
import EventBus from '../event-bus.js'

const localVue = createLocalVue()
localVue.use(Vuex)
Vue.use(Vuetify)

describe('ThreatIntel.vue', () => {
  let vuetify
  let store

  beforeEach(() => {
    vuetify = new Vuetify()
    vi.spyOn(ApiClient, 'getTagMetadata').mockReturnValue(new Promise(() => {}))
    store = new Vuex.Store({
      state: {
        sketch: { id: 1 },
        meta: {
          attributes: {
            intelligence: {
              ontology: 'intelligence',
              name: 'intelligence',
              value: {
                data: [
                  { ioc: '1.2.3.4', type: 'ipv4', tags: ['apt1'] },
                  { ioc: 'evil.com', type: 'fqdn', tags: ['apt1', 'phishing'] },
                ],
              },
            },
          },
        },
      },
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('searches for all indicators sharing a tag when its chip is clicked', async () => {
    const emitSpy = vi.spyOn(EventBus, '$emit')
    const wrapper = mount(ThreatIntel, {
      localVue,
      vuetify,
      store,
      stubs: { 'ts-indicator-dialog': true },
    })
    await wrapper.vm.$nextTick()

    const chip = wrapper.findAll('.v-chip').filter((c) => c.text() === 'apt1').at(0)
    await chip.trigger('click')

    const calls = emitSpy.mock.calls.filter((c) => c[0] === 'setQueryAndFilter')
    expect(calls).toHaveLength(1)
    expect(calls[0][1].doSearch).toBe(true)
    expect(calls[0][1].queryString).toBe('"1.2.3.4" OR "evil.com"')
  })
})
