import { mount, createLocalVue } from '@vue/test-utils'
import SearchDropdown from './SearchDropdown.vue'
import Vuetify from 'vuetify'
import Vuex from 'vuex'
import { vi, expect, it, describe, beforeEach } from 'vitest'
import Vue from 'vue'
import CompactNumber from '../../filters/CompactNumber.js'

const localVue = createLocalVue()
localVue.use(Vuex)
Vue.use(Vuetify)
Vue.filter(CompactNumber.name, CompactNumber.filter)

describe('SearchDropdown.vue', () => {
  let vuetify
  let store
  let state
  let actions

  beforeEach(() => {
    vuetify = new Vuetify()

    state = {
      sketch: { id: 1 },
      meta: {
        filter_labels: [
          { label: 'label1' },
          { label: 'label2' },
          { label: '__ts_fact_hidden' }, // should be filtered out
        ],
        mappings: [
          { field: 'field1', type: 'text' },
          { field: 'field2', type: 'string' },
        ],
        views: [
          { id: 1, name: 'view1' },
        ],
      },
      searchHistory: [],
      tags: [
        { tag: 'tag1' },
      ],
      dataTypes: [
        { data_type: 'type1', count: 10 },
      ],
      timeFilters: [
        { value: '2023-01-01,2023-01-02' },
      ],
    }

    actions = {
      updateTimeFilters: vi.fn(),
    }

    store = new Vuex.Store({
      state,
      actions,
    })
  })

  it('computes activeToken correctly for empty query', () => {
    const wrapper = mount(SearchDropdown, {
      localVue,
      vuetify,
      store,
      propsData: {
        queryString: '',
      },
      stubs: ['ts-tags-list'],
    })
    expect(wrapper.vm.activeToken).toBe('')
  })

  it('computes activeToken correctly for simple query', () => {
    const wrapper = mount(SearchDropdown, {
      localVue,
      vuetify,
      store,
      propsData: {
        queryString: 'field1',
      },
      stubs: ['ts-tags-list'],
    })
    expect(wrapper.vm.activeToken).toBe('field1')
  })

  it('computes activeToken correctly when query ends with space', () => {
    const wrapper = mount(SearchDropdown, {
      localVue,
      vuetify,
      store,
      propsData: {
        queryString: 'field1 ',
      },
      stubs: ['ts-tags-list'],
    })
    expect(wrapper.vm.activeToken).toBe('')
  })

  it('computes activeToken correctly for exact asterisk', () => {
    const wrapper = mount(SearchDropdown, {
      localVue,
      vuetify,
      store,
      propsData: {
        queryString: '*',
      },
      stubs: ['ts-tags-list'],
    })
    expect(wrapper.vm.activeToken).toBe('')
  })

  it('computes activeToken correctly for query ending with asterisk', () => {
    const wrapper = mount(SearchDropdown, {
      localVue,
      vuetify,
      store,
      propsData: {
        queryString: 'foo*',
      },
      stubs: ['ts-tags-list'],
    })
    expect(wrapper.vm.activeToken).toBe('foo*')
  })

  it('returns all matches when activeToken is empty (e.g. exact asterisk)', () => {
    const wrapper = mount(SearchDropdown, {
      localVue,
      vuetify,
      store,
      propsData: {
        queryString: '*',
      },
      stubs: ['ts-tags-list'],
    })
    expect(wrapper.vm.matches.fields).toHaveLength(2)
    expect(wrapper.vm.matches.tags).toHaveLength(1)
  })

  it('filters matches when activeToken is not empty', () => {
    const wrapper = mount(SearchDropdown, {
      localVue,
      vuetify,
      store,
      propsData: {
        queryString: 'field1',
      },
      stubs: ['ts-tags-list'],
    })
    expect(wrapper.vm.matches.fields).toHaveLength(1)
    expect(wrapper.vm.matches.fields[0].field).toBe('field1')
    expect(wrapper.vm.matches.tags).toHaveLength(0)
  })
})
