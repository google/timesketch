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

import { mount } from '@vue/test-utils';
import Vuetify from 'vuetify';
import Vue from 'vue';
import { describe, it, expect, beforeEach } from 'vitest';
import LinkRedirectWarning from './LinkRedirectWarning.vue';

Vue.use(Vuetify);

describe('LinkRedirectWarning.vue', () => {
  let vuetify;

  beforeEach(() => {
    vuetify = new Vuetify();
  });

  it('allows http/https contextUrl and does not double-escape ampersands', () => {
    const wrapper = mount(LinkRedirectWarning, {
      vuetify,
      propsData: {
        contextValue: 'a&b',
        contextUrl: 'https://example.com/lookup?q=a&b=1',
      },
    });

    expect(wrapper.vm.safeContextUrl).toBe('https://example.com/lookup?q=a&b=1');
    expect(wrapper.text()).toContain('https://example.com/lookup?q=a&b=1');
    expect(wrapper.text()).not.toContain('&amp;');

    const continueBtn = wrapper.findAll('.v-btn').at(1);
    expect(continueBtn.attributes('href')).toBe('https://example.com/lookup?q=a&b=1');
    expect(continueBtn.attributes('rel')).toBe('noopener noreferrer');
    expect(continueBtn.attributes('disabled')).toBeUndefined();
  });

  it('blocks non-http(s) schemes in contextUrl and disables continue button', () => {
    const wrapper = mount(LinkRedirectWarning, {
      vuetify,
      propsData: {
        contextValue: 'payload',
        contextUrl: 'javascript:alert(1)',
      },
    });

    expect(wrapper.vm.safeContextUrl).toBeNull();
    const continueBtn = wrapper.findAll('.v-btn').at(1);
    expect(continueBtn.attributes('href')).toBeUndefined();
    expect(continueBtn.attributes('disabled')).toBe('disabled');
  });
});
