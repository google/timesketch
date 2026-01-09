
import { mount, createLocalVue } from '@vue/test-utils'
import EventList from './EventList.vue'
import Vuetify from 'vuetify'
import Vuex from 'vuex'
import { vi, expect, it, describe, beforeEach, afterEach } from 'vitest'
import ApiClient from '../../utils/RestApiClient.js'
import Vue from 'vue'

// Mock RestApiClient
vi.mock('../../utils/RestApiClient.js', () => ({
  default: {
    exportSearchResult: vi.fn(() => Promise.resolve({ data: 'some-data' })),
    saveEventAnnotation: vi.fn(() => Promise.resolve({})),
    search: vi.fn(() => Promise.resolve({
        data: {
            objects: [],
            meta: {
                es_total_count: 0,
                es_total_count_complete: 0,
                es_time: 0,
                count_per_timeline: {},
                count_per_index: {},
            }
        }
    })),
    llmRequest: vi.fn(() => Promise.resolve({
        data: {
            response: 'summary',
            summary_event_count: 10,
            summary_unique_event_count: 5
        }
    }))
  }
}))

// Mock EventBus
vi.mock('../../event-bus.js', () => ({
  default: {
    $emit: vi.fn(),
    $on: vi.fn(),
    $off: vi.fn()
  }
}))

const localVue = createLocalVue()
localVue.use(Vuex)
Vue.use(Vuetify) // Use global Vue for Vuetify as per UploadFormButton.test.js

describe('EventList.vue', () => {
  let vuetify
  let store
  let state
  let actions

  beforeEach(() => {
    vuetify = new Vuetify()

    state = {
      sketch: { id: 1, active_timelines: [] },
      meta: { indices_metadata: {}, mappings: [] },
      currentSearchNode: { id: 1 },
      settings: { eventSummarization: false, showProcessingTimelineEvents: false },
      activeContext: {},
      enabledTimelines: []
    }

    actions = {
        updateSearchHistory: vi.fn(),
        updateTimeFilters: vi.fn(),
        updateEventLabels: vi.fn()
    }

    store = new Vuex.Store({
      state,
      actions
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('calls exportSearchResult when totalHits is <= 10000', async () => {
    const wrapper = mount(EventList, {
      localVue,
      vuetify,
      store,
      propsData: {
        queryRequest: {}
      },
      stubs: ['ts-bar-chart', 'ts-event-detail', 'ts-event-tag-menu', 'ts-event-tag-dialog', 'ts-event-action-menu', 'ts-event-tags', 'ts-explore-welcome-card', 'ts-search-not-found-card']
    })

    // Set eventList data to simulate totalHits
    await wrapper.setData({
      eventList: {
        meta: {
          es_total_count: 5000,
          es_total_count_complete: 0
        },
        objects: []
      }
    })

    // Call exportSearchResult
    await wrapper.vm.exportSearchResult()

    expect(ApiClient.exportSearchResult).toHaveBeenCalled()
  })

  it('does NOT call exportSearchResult and shows dialog when totalHits > 10000', async () => {
    const wrapper = mount(EventList, {
      localVue,
      vuetify,
      store,
      propsData: {
        queryRequest: {}
      },
      stubs: ['ts-bar-chart', 'ts-event-detail', 'ts-event-tag-menu', 'ts-event-tag-dialog', 'ts-event-action-menu', 'ts-event-tags', 'ts-explore-welcome-card', 'ts-search-not-found-card']
    })

    // Set eventList data to simulate totalHits > 10000
    await wrapper.setData({
      eventList: {
        meta: {
          es_total_count: 10001,
          es_total_count_complete: 0
        },
        objects: []
      }
    })

    // Call exportSearchResult
    await wrapper.vm.exportSearchResult()

    // Assert API is NOT called
    expect(ApiClient.exportSearchResult).not.toHaveBeenCalled()

    // Assert dialog is shown
    expect(wrapper.vm.showExportLimitDialog).toBe(true)
  })
})
