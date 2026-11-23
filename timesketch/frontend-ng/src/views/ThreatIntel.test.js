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

import { mount, createLocalVue } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vuex from 'vuex';
import Vue from 'vue';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import ThreatIntel from './ThreatIntel.vue';
import EventBus from '../event-bus.js';

vi.mock('../utils/RestApiClient.js', () => ({
  default: {
    getTagMetadata: vi.fn(() => Promise.resolve({ data: { default: { weight: 0, type: 'default' } } })),
    addSketchAttribute: vi.fn(() => Promise.resolve({})),
  },
}));

vi.mock('../event-bus.js', () => ({
  default: {
    $emit: vi.fn(),
    $on: vi.fn(),
    $off: vi.fn(),
  },
}));

const localVue = createLocalVue();
localVue.use(Vuex);
Vue.use(Vuetify);

describe('views/ThreatIntel.vue', () => {
  let vuetify;
  let store;

  beforeEach(() => {
    vuetify = new Vuetify();
    store = new Vuex.Store({
      state: {
        sketch: { id: 1 },
        meta: {
          attributes: {
            intelligence: {
              value: {
                data: [
                  { ioc: '8.8.8.8', type: 'ipv4', tags: ['suspicious'] },
                  { ioc: '8.8.4.4', type: 'ipv4', tags: ['suspicious'] },
                ],
              },
            },
          },
        },
      },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const mountView = () =>
    mount(ThreatIntel, {
      localVue,
      vuetify,
      store,
      stubs: ['ts-indicator-dialog'],
    });

  it('emits query_string searchMode for single IOC search', () => {
    const wrapper = mountView();
    wrapper.vm.generateSearchQuery('8.8.8.8');

    expect(EventBus.$emit).toHaveBeenCalledWith(
      'setQueryAndFilter',
      expect.objectContaining({
        doSearch: true,
        queryString: '"8.8.8.8"',
        searchMode: 'query_string',
      })
    );
  });

  it('resolves enriched tag objects and emits query_string searchMode', () => {
    const wrapper = mountView();
    wrapper.vm.searchForIOC({ name: 'suspicious', color: 'red', weight: 10 });

    expect(EventBus.$emit).toHaveBeenCalledWith(
      'setQueryAndFilter',
      expect.objectContaining({
        doSearch: true,
        queryString: '"8.8.8.8" OR "8.8.4.4"',
        searchMode: 'query_string',
      })
    );
  });
});
