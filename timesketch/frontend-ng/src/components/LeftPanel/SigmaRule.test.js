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
import SigmaRule from './SigmaRule.vue';

const localVue = createLocalVue();
localVue.use(Vuex);
Vue.use(Vuetify);

describe('SigmaRule.vue', () => {
  let vuetify;
  let store;

  beforeEach(() => {
    vuetify = new Vuetify();
    store = new Vuex.Store({
      state: {
        sketch: { id: 1 },
      },
    });
  });

  it('renders references as plain text rather than clickable links', async () => {
    const wrapper = mount(SigmaRule, {
      localVue,
      vuetify,
      store,
      propsData: {
        sigmaRule: {
          rule_uuid: '1234',
          title: 'Suspicious Rule',
        },
      },
      stubs: ['router-link'],
    });

    await wrapper.setData({
      expanded: true,
      detailedSigmaRule: {
        references: [
          'https://example.com/advisory',
          'javascript:alert(document.domain)',
        ],
      },
    });

    expect(wrapper.findAll('a').length).toBe(0);
    expect(wrapper.text()).toContain('https://example.com/advisory');
    expect(wrapper.text()).toContain('javascript:alert(document.domain)');
  });
});
