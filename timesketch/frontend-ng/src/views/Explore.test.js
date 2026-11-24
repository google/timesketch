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
import { describe, it, expect, beforeEach, vi } from 'vitest';
import Explore from './Explore.vue';

vi.mock('../utils/RestApiClient.js', () => ({
  default: {},
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

describe('views/Explore.vue searchMode', () => {
  let vuetify;

  beforeEach(() => {
    vuetify = new Vuetify();
  });

  const mountExplore = (stateOverrides = {}) => {
    const store = new Vuex.Store({
      state: {
        sketch: { id: 1, active_timelines: [] },
        meta: { supports_wildcard: false, indices_metadata: {} },
        searchHistory: [],
        settings: {},
        systemSettings: { OPENSEARCH_WILDCARD_DEFAULT: true },
        activeContext: {},
        enabledTimelines: [],
        ...stateOverrides,
      },
    });
    return mount(Explore, {
      localVue,
      vuetify,
      store,
      propsData: { sketchId: '1' },
      mocks: {
        $route: { name: 'Explore', query: {} },
        $router: { push: vi.fn() },
      },
      stubs: [
        'ts-search-history-tree',
        'ts-search-history-buttons',
        'ts-search-dropdown',
        'ts-timeline-picker',
        'ts-filter-menu',
        'ts-upload-timeline-form-button',
        'ts-add-manual-event',
        'ts-event-list',
        'ts-search-help-card',
        'ts-search-mode-toggle',
      ],
    });
  };

  it('forces query_string when supports_wildcard is false even if localSearchMode is wildcard', async () => {
    const wrapper = mountExplore({
      meta: { supports_wildcard: false, indices_metadata: {} },
    });
    await wrapper.setData({ localSearchMode: 'wildcard' });
    expect(wrapper.vm.searchMode).toBe('query_string');
  });

  it('honors localSearchMode and OPENSEARCH_WILDCARD_DEFAULT when supports_wildcard is true', async () => {
    const wrapper = mountExplore({
      meta: { supports_wildcard: true, indices_metadata: {} },
    });
    expect(wrapper.vm.searchMode).toBe('wildcard');

    await wrapper.setData({ localSearchMode: 'query_string' });
    expect(wrapper.vm.searchMode).toBe('query_string');
  });
});
