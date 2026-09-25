import { mount, shallowMount, createLocalVue } from '@vue/test-utils'
import Vuetify from 'vuetify'
import Vuex from 'vuex'
import Vue from 'vue'
import { expect, it, describe } from 'vitest'
import SearchModeToggle from './SearchModeToggle.vue'

const localVue = createLocalVue()
localVue.use(Vuex)
Vue.use(Vuetify)

const mountToggle = ({ supportsWildcard = false, directQueryEnabled = false } = {}) =>
  shallowMount(SearchModeToggle, {
    localVue,
    vuetify: new Vuetify(),
    store: new Vuex.Store({ state: { meta: { supports_wildcard: supportsWildcard } } }),
    propsData: { value: 'query_string', directQueryEnabled },
  })

// The activator lives in a scoped slot of v-menu, which shallowMount stubs
// away, so anything asserting on the rendered button needs a full mount.
const mountActivator = ({ supportsWildcard = false, directQueryEnabled = false } = {}) =>
  mount(SearchModeToggle, {
    localVue,
    vuetify: new Vuetify(),
    store: new Vuex.Store({ state: { meta: { supports_wildcard: supportsWildcard } } }),
    propsData: { value: 'query_string', directQueryEnabled },
  }).find('button')

const values = (wrapper) => wrapper.vm.menuItems.map((item) => item.value)

describe('SearchModeToggle.vue direct-query gating', () => {
  it('offers PPL and SQL when the cluster supports them', () => {
    expect(values(mountToggle({ directQueryEnabled: true }))).toEqual(['query_string', 'ppl', 'sql'])
  })

  it('drops PPL and SQL when the cluster does not', () => {
    expect(values(mountToggle())).toEqual(['query_string'])
  })

  it('gates PPL and SQL independently of wildcard support', () => {
    expect(values(mountToggle({ supportsWildcard: true }))).toEqual(['query_string', 'wildcard'])
    expect(values(mountToggle({ supportsWildcard: true, directQueryEnabled: true }))).toEqual([
      'query_string',
      'wildcard',
      'ppl',
      'sql',
    ])
  })

  it('cannot open the menu when only query string is left', () => {
    expect(mountToggle().vm.canOpenMenu).toBe(false)
    expect(mountToggle({ directQueryEnabled: true }).vm.canOpenMenu).toBe(true)
  })

  it('keeps the wildcard reset, but only for wildcard', async () => {
    const wrapper = mountToggle({ supportsWildcard: true, directQueryEnabled: true })

    wrapper.vm.selectItem({ value: 'wildcard' })
    wrapper.vm.$store.state.meta.supports_wildcard = false
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.selectedValue).toBe('query_string')

    wrapper.vm.$store.state.meta.supports_wildcard = true
    await wrapper.vm.$nextTick()
    wrapper.vm.selectItem({ value: 'ppl' })
    wrapper.vm.$store.state.meta.supports_wildcard = false
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.selectedValue).toBe('ppl')
  })
})

// On a cluster without PPL and SQL the selector is a wildcard toggle and
// nothing more, so these pin the behaviour a wildcard-only sketch relies on.
describe('SearchModeToggle.vue without direct query', () => {
  it('opens the menu only when wildcard is supported', () => {
    expect(mountToggle({ supportsWildcard: true }).vm.canOpenMenu).toBe(true)
    expect(mountToggle({ supportsWildcard: false }).vm.canOpenMenu).toBe(false)
  })

  it('greys the activator and hides the chevron when wildcard is unsupported', () => {
    const btn = mountActivator({ supportsWildcard: false })
    expect(btn.attributes('style')).toContain('opacity: 0.8')
    expect(btn.attributes('style')).toContain('cursor: default')
    expect(btn.attributes('title')).toBe('This sketch does not support wildcard searches')
    expect(btn.find('.v-icon').exists()).toBe(false)
  })

  it('leaves the activator untouched when wildcard is supported', () => {
    const btn = mountActivator({ supportsWildcard: true })
    expect(btn.attributes('style')).not.toContain('opacity')
    expect(btn.attributes('style')).not.toContain('cursor')
    expect(btn.attributes('title')).toBe('Query String')
    expect(btn.find('.v-icon').exists()).toBe(true)
  })
})
