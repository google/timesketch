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
import { describe, it, expect, beforeEach } from 'vitest';
import SearchNotFoundCard from './SearchNotFoundCard.vue';

const localVue = createLocalVue();
localVue.use(Vuex);
Vue.use(Vuetify);

describe('SearchNotFoundCard.vue', () => {
  let vuetify;
  let store;

  beforeEach(() => {
    vuetify = new Vuetify();
    store = new Vuex.Store({
      state: {
        tags: [],
        dataTypes: [],
        meta: { filter_labels: [], views: [] },
      },
    });
  });

  const mountCard = (props = {}) =>
    mount(SearchNotFoundCard, {
      localVue,
      vuetify,
      store,
      propsData: {
        currentQueryString: '8.8.8.8',
        ...props,
      },
      stubs: {
        'ts-search-guide-card': {
          name: 'TsSearchGuideCard',
          props: ['searchMode'],
          template: '<div class="guide-stub" :data-mode="searchMode"><slot name="header"></slot></div>',
        },
      },
    });

  it('forwards wildcard searchMode and shows wildcard suggestions', () => {
    const wrapper = mountCard({ searchMode: 'wildcard' });
    expect(wrapper.find('.guide-stub').attributes('data-mode')).toBe('wildcard');
    expect(wrapper.text()).toContain('Wrap search terms with wildcards');
    expect(wrapper.text()).toContain('*searchterm*');
  });

  it('defaults to query_string searchMode and shows classic suggestions', () => {
    const wrapper = mountCard();
    expect(wrapper.find('.guide-stub').attributes('data-mode')).toBe('query_string');
    expect(wrapper.text()).toContain('Try different keywords');
    expect(wrapper.text()).not.toContain('Wrap search terms with wildcards');
  });
});
