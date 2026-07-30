import { shallowMount, createLocalVue } from '@vue/test-utils'
import Vuetify from 'vuetify'
import Vue from 'vue'
import { expect, it, describe, beforeEach } from 'vitest'
import DirectQueryTable from './DirectQueryTable.vue'
import EventBus from '../../event-bus.js'

const localVue = createLocalVue()
Vue.use(Vuetify)

const mountTable = (columns, datarows) =>
  shallowMount(DirectQueryTable, {
    localVue,
    vuetify: new Vuetify(),
    propsData: { columns, datarows, total: datarows.length, language: 'ppl' },
  })

// The component keys rows by column position, so a fixture row is addressed the
// same way the template addresses it.
const rowItem = (wrapper, rowIndex) => wrapper.vm.tableRows[rowIndex]

describe('DirectQueryTable.vue pivot', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mountTable(['username', 'cnt'], [['analyst@example.com', 42], ['', 7]])
  })

  it('offers a pivot on a field column', () => {
    expect(wrapper.vm.canPivot(rowItem(wrapper, 0), 0)).toBe(true)
  })

  it('does not offer a pivot on a numeric aggregate column', () => {
    expect(wrapper.vm.canPivot(rowItem(wrapper, 0), 1)).toBe(false)
  })

  it('does not offer a pivot on an empty value', () => {
    expect(wrapper.vm.canPivot(rowItem(wrapper, 1), 0)).toBe(false)
  })

  it('does not offer a pivot on a value past the keyword ignore_above limit', () => {
    const w = mountTable(['path'], [['a'.repeat(256)], ['b'.repeat(257)]])
    expect(w.vm.canPivot(rowItem(w, 0), 0)).toBe(true)
    expect(w.vm.canPivot(rowItem(w, 1), 0)).toBe(false)
  })

  it('does not offer a pivot on an aggregate expression column', () => {
    const w = mountTable(['count()', 'span(datetime,1h)'], [['x', 'y']])
    expect(w.vm.canPivot(rowItem(w, 0), 0)).toBe(false)
    expect(w.vm.canPivot(rowItem(w, 0), 1)).toBe(false)
  })

  it('emits a term chip that the event list understands', () => {
    let received = null
    EventBus.$once('setQueryAndFilter', (event) => {
      received = event
    })

    wrapper.vm.pivot(rowItem(wrapper, 0), 0)

    expect(received).toEqual({
      doSearch: true,
      chip: {
        field: 'username',
        value: 'analyst@example.com',
        type: 'term',
        operator: 'must',
        active: true,
      },
    })
  })
})
