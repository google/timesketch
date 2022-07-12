import { expect } from 'chai'
import { shallowMount } from '@vue/test-utils'

import Intelligence from '@/views/Intelligence'

describe('Intelligence.vue', () => {
  it('should correctly do something', () => {
    let wrapper = shallowMount(Intelligence, {})
    expect(wrapper.findAll('.container p.card-header-title').at(0).text()).toBe('Indicators of compromise')
  })
})
