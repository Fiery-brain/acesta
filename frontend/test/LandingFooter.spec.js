import { mount } from '@vue/test-utils'
import LandingFooter from '~/components/LandingFooter.vue'

describe('LandingFooter', () => {
    test('is a Vue instance', () => {
        const wrapper = mount(LandingFooter)
        expect(wrapper.vm).toBeTruthy()
    })
})