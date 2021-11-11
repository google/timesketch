import { expect } from 'chai'
import { shallowMount } from '@vue/test-utils'
import TsIOCMenu from '@/components/Common/TsIOCMenu.vue'


const testIOCs = [

    // We only want to pick up correclty formatted IP addresses
    {text: '127.0.0.1', type: 'ip'},
    {text: '127.0.0.01', type: 'other'},
    {text: '266.0.0.1', type: 'other'},

    // Test hash parsing with wrong length (prepend 00) and non-hex chars (ZZ)
    {text: '819f04e5706f509de5a6b833d3f561369156820b4240c7c26577b223e59aae97', type: 'hash_sha256'},
    {text: '00819f04e5706f509de5a6b833d3f561369156820b4240c7c26577b223e59aae97', type: 'other'},
    {text: 'ZZ9f04e5706f509de5a6b833d3f561369156820b4240c7c26577b223e59aae97', type: 'other'},

    // sha1
    {text: 'e6e8ea7465f12e4d3b5a067a4c4dc698436b3478', type: 'hash_sha1'},
    {text: '00e6e8ea7465f12e4d3b5a067a4c4dc698436b3478', type: 'other'},
    {text: 'ZZe8ea7465f12e4d3b5a067a4c4dc698436b3478', type: 'other'},

    // md5
    {text: '11a3e229084349bc25d97e29393ced1d', type: 'hash_md5'},
    {text: '0011a3e229084349bc25d97e29393ced1d', type: 'other'},
    {text: 'ZZa3e229084349bc25d97e29393ced1d', type: 'other'},
]

describe('TsIOCMenu.vue', () => {
  it('IOC type is correctly derived from text selection', () => {
    const wrapper = shallowMount(TsIOCMenu, {})
    for (let testIoc of testIOCs) {
        expect(wrapper.vm.getIOC(testIoc.text).type).to.equal(testIoc.type, testIoc.text)
    }
  })
})
