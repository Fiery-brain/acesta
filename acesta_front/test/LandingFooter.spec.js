import { mount } from '@vue/test-utils'
import Logo from '@/components/LandingFooter.vue'

describe('LandingFooter', () => {
    test('is a Vue instance', () => {
        const wrapper = mount(Logo)
        expect(wrapper.vm).toBeTruthy()
    })
})